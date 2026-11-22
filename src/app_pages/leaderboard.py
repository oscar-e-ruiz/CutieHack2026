# Leaderboard page: ranked watcher scores.

import streamlit as st

from service import get_client

st.title("Leaderboard")

response = (
    get_client()
    .table("users")
    .select("display_name, score")
    .not_.is_("score", "null")
    .order("score", desc=True)
    .order("display_name")
    .limit(10)
    .execute()
)

if not response.data:
    st.info("No scores to display yet.")
else:
    st.dataframe(
        [
            {"Rank": rank, "User": user["display_name"], "Score": user["score"]}
            for rank, user in enumerate(response.data, start=1)
        ],
        hide_index=True,
        column_config={
            "Rank": st.column_config.NumberColumn(alignment="left"),
            "User": st.column_config.TextColumn(alignment="left"),
            "Score": st.column_config.NumberColumn(alignment="left"),
        },
        width="stretch",
    )
