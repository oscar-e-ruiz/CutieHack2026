# Supabase-backed helpers: auth, profile lookup, and sighting submit.

from dataclasses import asdict
from datetime import datetime, timezone
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
    return Sighting(
        id=str(row["id"]),
        user_id=row["user_id"],
        photo_url=row["photo_url"],
        captured_at=_parse_datetime(row["captured_at"]),
        submitted_at=_parse_datetime(row["submitted_at"]),
        latitude=float(row["latitude"]),
        longitude=float(row["longitude"]),
        gps_accuracy=float(row["gps_accuracy"]),
        group_size=int(row["group_size"]),
        behavior=row["behavior"],
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
