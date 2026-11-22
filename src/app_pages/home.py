# Home page: greeting for the signed-in user and a link to profile/settings.

import streamlit as st

user = st.session_state.user  # Set in streamlit_app.py after login
st.title(f"Hi, {user.display_name}")
st.page_link("app_pages/profile.py", label="Profile and settings")
