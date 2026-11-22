# Export page — researcher CSV download of all burro sightings.
#
# Story notes:
# - One-click download via st.download_button.
# - Show a clear empty state when there are no rows yet.
# - CSV is built in BurroWatchService.export_csv() (exact coords, user_id = Google sub).
# - Demo: available to every signed-in user (no researcher-email gate).

import streamlit as st

from service import BurroWatchService

st.title("Export")
st.caption("Download all sightings as CSV for research use.")

service = BurroWatchService()

# Fresh build each run so new Home submits show up without a hard refresh.
csv_text = None
load_error = None
try:
    csv_text = service.export_csv()
except Exception as exc:
    # Surface Supabase / schema problems instead of a blank page.
    load_error = str(exc)

if load_error:
    st.error(f"Could not build export: {load_error}")
elif csv_text:
    # Filename is stable for demos; overwrite is fine for researchers re-downloading.
    st.download_button(
        label="Download sightings CSV",
        data=csv_text,
        file_name="burrowatch_sightings.csv",
        mime="text/csv",
        help="Exact GPS coordinates; users identified by Google sub only.",
    )
    st.success("Export ready. Columns include sighting_id, user_id, times, GPS, and behavior.")
else:
    # export_csv() returns None when Sightings is empty.
    st.info("No sightings to export yet. Submit one from Home, then come back here.")

# Navigation back into the rest of the app.
st.page_link("app_pages/home.py", label="Home")
st.page_link("app_pages/live_map.py", label="Sightings Map")
st.page_link("app_pages/leaderboard.py", label="Leaderboard")
