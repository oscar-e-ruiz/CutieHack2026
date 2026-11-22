# Profile page: photo, display name, score, and sign-out.

import streamlit as st

user = st.session_state.user  # Set in streamlit_app.py after login

if user.profile_photo_url:
    st.image(user.profile_photo_url, width=96)
st.header(user.display_name)
st.metric("Score", user.score)

st.button("Sign out", on_click=st.logout)
