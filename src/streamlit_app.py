import streamlit as st

from service import BurroWatchService

st.set_page_config(page_title="BurroWatch UCR")

service = BurroWatchService()
user = service.login()

if user is None:
    st.title("BurroWatch UCR")
    st.write("Report burro sightings from a safe distance and earn points.")
    st.button("Sign in with Google", on_click=st.login)
    st.stop()

st.session_state.user = user

page = st.navigation([
    st.Page("app_pages/home.py", title="Home", default=True),
    st.Page("app_pages/profile.py", title="Profile and settings"),
])
page.run()