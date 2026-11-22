import pandas as pd
import streamlit as st

from service import get_client

st.title("Live sightings map")
st.caption("Updates every 10 seconds.")


@st.fragment(run_every=10)
def sightings_map() -> None:
    rows = []
    page_size = 1000
    while True:
        response = (
            get_client()
            .table("Sightings")
            .select("latitude, longitude", count="exact")
            .order("latitude")
            .order("longitude")
            .range(len(rows), len(rows) + page_size - 1)
            .execute()
        )
        if response.count is None:
            raise RuntimeError("Could not determine the number of sightings.")
        if not response.data and len(rows) < response.count:
            raise RuntimeError("Could not retrieve all sighting coordinates.")
        rows.extend(response.data)
        if len(rows) >= response.count:
            break

    if not rows:
        st.info("No sightings to display yet.")
        return

    coordinates = pd.DataFrame(rows)
    coordinates["latitude"] = pd.to_numeric(coordinates["latitude"], errors="coerce")
    coordinates["longitude"] = pd.to_numeric(coordinates["longitude"], errors="coerce")
    valid = coordinates["latitude"].between(-90, 90) & coordinates["longitude"].between(-180, 180)
    if not valid.all():
        st.warning(f"{(~valid).sum()} sightings have invalid coordinates and are not shown.")
    if not valid.any():
        st.info("No sightings with valid coordinates to display.")
        return

    st.map(coordinates.loc[valid, ["latitude", "longitude"]], size=20)


sightings_map()