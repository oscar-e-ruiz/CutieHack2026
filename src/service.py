# Supabase-backed helpers: auth, profile lookup, sighting submit, map, and CSV export.

import csv
import io
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import streamlit as st
from supabase import Client, create_client

from models import Sighting, User

# Columns fetched for User; keep in sync with models.User fields.
USER_COLUMNS = "id, display_name, profile_photo_url, score"
SIGHTING_COLUMNS = (
    "id, user_id, photo_url, captured_at, submitted_at, latitude, longitude, "
    "gps_accuracy, group_size, behavior, points_earned"
)
PHOTOS_BUCKET = "photos"
BEHAVIORS = ("grazing", "resting", "walking", "other", "unknown")


@st.cache_resource
def get_client() -> Client:
    """Shared Supabase client (cached for the Streamlit process lifetime)."""
    return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["secret_key"])


def short_name() -> str:
    """Build a short display name from Google profile claims (e.g. 'Alex R.')."""
    first = st.user.get("given_name") or st.user.get("name") or "Burro Watcher"
    last = st.user.get("family_name")
    return f"{first} {last[0]}." if last else first


def _parse_datetime(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _row_to_sighting(row: dict) -> Sighting:
    captured_at = _parse_datetime(row["captured_at"])
    submitted_raw = row.get("submitted_at") or row["captured_at"]
    return Sighting(
        id=str(row["id"]),
        user_id=row["user_id"],
        photo_url=row.get("photo_url") or "",
        captured_at=captured_at,
        submitted_at=_parse_datetime(submitted_raw),
        latitude=float(row["latitude"]),
        longitude=float(row["longitude"]),
        gps_accuracy=float(row["gps_accuracy"] or 0),
        group_size=int(row["group_size"] or 1),
        behavior=row.get("behavior") or "unknown",
        points_earned=int(row.get("points_earned") or 0),
    )


class BurroWatchService:
    """App service layer over Supabase users, sightings, and photo storage."""

    def __init__(self) -> None:
        self.db = get_client()

    def login(self) -> User | None:
        """Return the current user if signed in; create a DB row on first login."""
        if not st.user.is_logged_in:
            return None

        existing = self.get_profile(st.user.sub)
        if existing is not None:
            return existing

        # First visit: seed a profile from Google OAuth claims.
        user = User(
            id=st.user.sub,
            display_name=short_name(),
            profile_photo_url=st.user.get("picture"),
        )
        self.db.table("users").insert(asdict(user)).execute()
        return user

    def get_profile(self, user_id: str) -> User | None:
        """Load a user by id, or None if no matching row."""
        rows = self.db.table("users").select(USER_COLUMNS).eq("id", user_id).execute().data
        return User(**rows[0]) if rows else None

    def submit_sighting(
        self,
        *,
        user_id: str,
        photo: bytes,
        captured_at: datetime,
        latitude: float,
        longitude: float,
        gps_accuracy: float,
        group_size: int,
        behavior: str,
    ) -> Sighting:
        """Upload the photo, insert a Sightings row, and return the saved sighting."""
        if behavior not in BEHAVIORS:
            raise ValueError(f"Unknown behavior: {behavior}")
        if group_size < 1:
            raise ValueError("group_size must be at least 1")

        photo_path = f"{uuid4()}.jpg"
        self.db.storage.from_(PHOTOS_BUCKET).upload(
            photo_path,
            photo,
            file_options={"content-type": "image/jpeg", "upsert": "false"},
        )
        photo_url = self.db.storage.from_(PHOTOS_BUCKET).get_public_url(photo_path)

        if captured_at.tzinfo is None:
            captured_at = captured_at.replace(tzinfo=timezone.utc)

        payload = {
            "user_id": user_id,
            "photo_url": photo_url,
            "captured_at": captured_at.isoformat(),
            "latitude": latitude,
            "longitude": longitude,
            "gps_accuracy": gps_accuracy,
            "group_size": group_size,
            "behavior": behavior,
            "points_earned": 0,
        }
        rows = (
            self.db.table("Sightings")
            .insert(payload)
            .execute()
            .data
        )
        if not rows:
            # Some setups omit RETURNING; fetch the newest row for this user + photo.
            rows = (
                self.db.table("Sightings")
                .select(SIGHTING_COLUMNS)
                .eq("user_id", user_id)
                .eq("photo_url", photo_url)
                .order("submitted_at", desc=True)
                .limit(1)
                .execute()
                .data
            )
        if not rows:
            raise RuntimeError("Sighting insert did not return a row.")
        return _row_to_sighting(rows[0])

    def get_map_sightings(self, days: int = 7) -> list[Sighting]:
        """Return recent sightings with coordinates rounded to ~100 m for the public map."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        rows = (
            self.db.table("Sightings")
            .select(SIGHTING_COLUMNS)
            .gte("captured_at", cutoff.isoformat())
            .order("captured_at", desc=True)
            .execute()
            .data
        ) or []

        sightings: list[Sighting] = []
        for row in rows:
            sighting = _row_to_sighting(row)
            sightings.append(
                Sighting(
                    id=sighting.id,
                    user_id=sighting.user_id,
                    photo_url=sighting.photo_url,
                    captured_at=sighting.captured_at,
                    submitted_at=sighting.submitted_at,
                    # Public map: round to 3 decimals (~100 m), unlike CSV export.
                    latitude=round(sighting.latitude, 3),
                    longitude=round(sighting.longitude, 3),
                    gps_accuracy=sighting.gps_accuracy,
                    group_size=sighting.group_size,
                    behavior=sighting.behavior,
                    points_earned=sighting.points_earned,
                )
            )
        return sightings

    def export_csv(self) -> str | None:
        """Build a researcher CSV of all sightings, or None when the table is empty.

        Notes:
        - Uses exact coordinates (not the rounded map values).
        - Identifies people only by Google `sub` in user_id — no names or emails.
        - Header names match the handoff export spec (gps_accuracy_m, sighting_id).
        """
        # Pull every sighting; order oldest-first so the CSV reads chronologically.
        rows = (
            self.db.table("Sightings")
            .select(SIGHTING_COLUMNS)
            .order("captured_at", desc=False)
            .execute()
            .data
        ) or []

        # Empty table → page should show a clear "no data" message instead of a blank file.
        if not rows:
            return None

        sightings = [_row_to_sighting(row) for row in rows]

        # csv module + StringIO keeps us dependency-free (no pandas required here).
        buffer = io.StringIO()
        writer = csv.DictWriter(
            buffer,
            fieldnames=[
                "sighting_id",
                "user_id",
                "captured_at",
                "submitted_at",
                "latitude",
                "longitude",
                "gps_accuracy_m",
                "group_size",
                "behavior",
                "photo_url",
                "points_earned",
            ],
        )
        writer.writeheader()

        for sighting in sightings:
            writer.writerow(
                {
                    "sighting_id": sighting.id,
                    "user_id": sighting.user_id,  # Google sub only
                    "captured_at": sighting.captured_at.isoformat(),
                    "submitted_at": sighting.submitted_at.isoformat(),
                    "latitude": sighting.latitude,  # exact coords for research
                    "longitude": sighting.longitude,
                    "gps_accuracy_m": sighting.gps_accuracy,
                    "group_size": sighting.group_size,
                    "behavior": sighting.behavior,
                    "photo_url": sighting.photo_url,
                    "points_earned": sighting.points_earned,
                }
            )

        return buffer.getvalue()
