from dataclasses import asdict

import streamlit as st
from supabase import Client, create_client

from models import User

USER_COLUMNS = "id, display_name, profile_photo_url, score"


@st.cache_resource
def get_client() -> Client:
    return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["secret_key"])


def short_name() -> str:
    first = st.user.get("given_name") or st.user.get("name") or "Burro Watcher"
    last = st.user.get("family_name")
    return f"{first} {last[0]}." if last else first


class BurroWatchService:
    def __init__(self) -> None:
        self.db = get_client()

    def login(self) -> User | None:
        if not st.user.is_logged_in:
            return None

        existing = self.get_profile(st.user.sub)
        if existing is not None:
            return existing

        user = User(
            id=st.user.sub,
            display_name=short_name(),
            profile_photo_url=st.user.get("picture"),
        )
        self.db.table("users").insert(asdict(user)).execute()
        return user

    def get_profile(self, user_id: str) -> User | None:
        rows = self.db.table("users").select(USER_COLUMNS).eq("id", user_id).execute().data
        return User(**rows[0]) if rows else None