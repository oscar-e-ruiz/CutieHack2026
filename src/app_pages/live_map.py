# Live map: recent submitted sightings from Supabase via BurroWatchService.

import pandas as pd
import streamlit as st

from service import BurroWatchService

st.title("Sightings Map")
st.caption("Past 7 days · updates every 10 seconds · locations rounded to ~100 m.")

service = BurroWatchService()


@st.fragment(run_every=10)
def sightings_map() -> None:
    try:
        sightings = service.get_map_sightings(days=7)
    except Exception as exc:
        st.error(f"Could not load sightings: {exc}")
        return

    if not sightings:
        st.info("No sightings to display yet. Submit one from Home.")
        return

    coordinates = pd.DataFrame(
        {
            "latitude": [s.latitude for s in sightings],
            "longitude": [s.longitude for s in sightings],
        }
    )
    valid = coordinates["latitude"].between(-90, 90) & coordinates["longitude"].between(
        -180, 180
    )
    if not valid.all():
        st.warning(f"{(~valid).sum()} sightings have invalid coordinates and are not shown.")
    if not valid.any():
        st.info("No sightings with valid coordinates to display.")
        return

    st.map(coordinates.loc[valid, ["latitude", "longitude"]], size=20)

    st.subheader(f"Recent sightings ({len(sightings)})")
    for sighting in sightings[:20]:
        when = sighting.captured_at.strftime("%Y-%m-%d %H:%M UTC")
        st.write(
            f"{when} · group of {sighting.group_size} · {sighting.behavior}"
        )


sightings_map()


