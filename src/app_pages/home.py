import streamlit as st

user = st.session_state.user
st.title(f"Hi, {user.display_name}")
st.page_link("app_pages/profile.py", label="Profile and settings")