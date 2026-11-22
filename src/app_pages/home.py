# Home page — capture a sighting (camera + GPS + form) and navigate the app.
# AC: profile picture, name, take photo, profile settings, leaderboard,
#     sightings map, logout.

import hashlib
from datetime import datetime, timezone

import streamlit as st
from streamlit_js_eval import get_geolocation

from service import BEHAVIORS, BurroWatchService

user = st.session_state.user  # Set in streamlit_app.py after login
service = BurroWatchService()

# Profile picture
if user.profile_photo_url:
    st.image(user.profile_photo_url, width=96)

# Name
st.title(f"Hi, {user.display_name}")

if st.session_state.pop("flash_success", None):
    st.success("Sighting saved.")

st.info(
    "Stay back, don't feed, and don't touch wild burros. "
    "Only report from a safe distance."
)
st.caption("Tip: use Switch camera for the back camera on your phone.")

if "camera_key" not in st.session_state:
    st.session_state.camera_key = 0
if "submitted_photo_hash" not in st.session_state:
    st.session_state.submitted_photo_hash = None
if "capture_times" not in st.session_state:
    st.session_state.capture_times = {}

# Take photo (on homepage)
photo = st.camera_input("Take photo", key=f"home_camera_{st.session_state.camera_key}")

if photo is not None:
    photo_bytes = photo.getvalue()
    photo_hash = hashlib.sha256(photo_bytes).hexdigest()

    # Record capture time once per photo (server clock).
    if photo_hash not in st.session_state.capture_times:
        st.session_state.capture_times[photo_hash] = datetime.now(timezone.utc)
    captured_at = st.session_state.capture_times[photo_hash]

    # Fresh location key per photo so GPS is re-requested after a retake.
    location = get_geolocation(component_key=f"geo_{photo_hash[:16]}")

    latitude = longitude = accuracy = None
    if location is None:
        st.info("Finding your location…")
        if st.button("Try again", key="retry_location"):
            st.rerun()
    elif "error" in location:
        code = location["error"].get("code")
        if code == 1:
            st.error(
                "Location permission denied. Enable location for this site in "
                "your browser settings, then try again."
            )
        else:
            st.warning(location["error"].get("message", "Could not get location."))
        if st.button("Try again", key="retry_location_error"):
            st.rerun()
    else:
        coords = location["coords"]
        latitude = float(coords["latitude"])
        longitude = float(coords["longitude"])
        accuracy = float(coords.get("accuracy") or 0)
        st.success(f"Location ready — within {accuracy:.0f} m.")

    with st.form("submit_sighting"):
        group_size = st.number_input("Group size", min_value=1, step=1, value=1)
        behavior = st.selectbox("Behavior", BEHAVIORS)
        submitted = st.form_submit_button("Submit sighting")

    if submitted:
        if st.session_state.submitted_photo_hash == photo_hash:
            st.warning("This photo was already submitted.")
        elif latitude is None or longitude is None or accuracy is None:
            st.error("Need a location before you can submit.")
        else:
            try:
                sighting = service.submit_sighting(
                    user_id=user.id,
                    photo=photo_bytes,
                    captured_at=captured_at,
                    latitude=latitude,
                    longitude=longitude,
                    gps_accuracy=accuracy,
                    group_size=int(group_size),
                    behavior=behavior,
                )
            except Exception as exc:
                st.error(f"Could not save sighting: {exc}")
            else:
                st.session_state.submitted_photo_hash = photo_hash
                st.session_state.flash_success = True
                # Remount camera so the next report starts clean.
                st.session_state.camera_key += 1
                st.rerun()



# Logout
st.button("Sign out", on_click=st.logout)
