# Export page: CSV download of sightings (stub until export_csv is built).

import streamlit as st

st.title("Export")
st.write("CSV download of sightings will appear here.")

st.page_link("app_pages/home.py", label="Home")
st.page_link("app_pages/live_map.py", label="Sightings Map")
st.page_link("app_pages/leaderboard.py", label="Leaderboard")
