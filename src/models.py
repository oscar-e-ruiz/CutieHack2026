# Data models shared across the app (User shape mirrors the Supabase users table).

from dataclasses import dataclass


@dataclass
class User:
    """A BurroWatch account: identity, display info, and points score."""

    id: str  # Auth subject (st.user.sub) — primary key in Supabase
    display_name: str
    profile_photo_url: str | None
    score: int = 0  # Points earned from reporting burro sightings
