# BurroWatch UCR

Cutie Hack 2026 Streamlit app for reporting wild burro sightings at UC Riverside.
Signed-in students capture an in-app photo with GPS, group size, and behavior;
sightings show on a live map and can be exported as CSV for research.

## Features
- Google sign-in (`st.login`); creates a Supabase `users` row on first login
- Home: profile photo, name, safety note, camera, GPS, submit form, logout
- Sightings Map: past 7 days, coords rounded to ~100 m, auto-refresh
- Export: researcher CSV with exact coordinates (user id = Google `sub` only)
- Leaderboard: top scores (if enabled in current branch)
- Profile: photo, name, score, sign out

## Stack
- Python 3.12 + uv
- Streamlit (`streamlit[auth]`)
- Supabase (Postgres + Storage `photos` bucket)
- `streamlit-js-eval` for browser GPS

## Run locally
```bash
uv sync
uv run streamlit run src/streamlit_app.py