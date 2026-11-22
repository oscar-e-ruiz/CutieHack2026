# Home page — user story: homescreen so the user can interact with the app.
# AC: profile picture, name, take photo, profile settings, leaderboard,
#     sightings map, logout.

import streamlit as st

user = st.session_state.user  # Set in streamlit_app.py after login

# Profile picture
if user.profile_photo_url:
    st.image(user.profile_photo_url, width=96)

# Name
st.title(f"Hi, {user.display_name}")

# Take photo (on homepage)
st.camera_input("Take photo")

# Profile settings / leaderboard / sightings map
st.page_link("app_pages/profile.py", label="Profile and settings")
st.page_link("app_pages/leaderboard.py", label="Leaderboard")
st.page_link("app_pages/live_map.py", label="Sightings Map")

# Logout
st.button("Sign out", on_click=st.logout)
