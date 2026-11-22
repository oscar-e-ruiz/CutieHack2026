# Supabase-backed helpers: auth bootstrap, profile lookup, and first-time user insert.

from dataclasses import asdict

import streamlit as st
from supabase import Client, create_client

from models import User

# Columns fetched for User; keep in sync with models.User fields.
USER_COLUMNS = "id, display_name, profile_photo_url, score"


@st.cache_resource
def get_client() -> Client:
    """Shared Supabase client (cached for the Streamlit process lifetime)."""
    return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["secret_key"])


def short_name() -> str:
    """Build a short display name from Google profile claims (e.g. 'Alex R.')."""
    first = st.user.get("given_name") or st.user.get("name") or "Burro Watcher"
    last = st.user.get("family_name")
    return f"{first} {last[0]}." if last else first


class BurroWatchService:
    """App service layer over the Supabase users table."""

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
