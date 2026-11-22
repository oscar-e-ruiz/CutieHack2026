import tomllib
import uuid
from datetime import datetime, timezone

from supabase import create_client

with open(".streamlit/secrets.toml", "rb") as file:
    settings = tomllib.load(file)["supabase"]

client = create_client(settings["SUPABASE_URL"], settings["SUPABASE_KEY"])

coordinates = [
    (33.9737, -117.3281),
    (33.9745, -117.3287),
    (33.9729, -117.3274),
    (33.9751, -117.3268),
    (33.9722, -117.3291),
    (33.9740, -117.3300),
    (33.9718, -117.3265),
    (33.9760, -117.3295),
    (33.9733, -117.3258),
    (33.9752, -117.3310),
]
captured_at = datetime.now(timezone.utc).isoformat()
sightings = [
    {
        "user_id": str(uuid.uuid4()),
        "photo_url": "https://example.com/test-photo.jpg",
        "captured_at": captured_at,
        "latitude": latitude,
        "longitude": longitude,
    }
    for latitude, longitude in coordinates
]

client.table("Sightings").insert(sightings, returning="minimal").execute()
print(f"Inserted {len(sightings)} test sightings.")

response = (
    client.table("Sightings")
    .select("*")
    .in_("user_id", [sighting["user_id"] for sighting in sightings])
    .execute()
)

if len(response.data) != len(sightings):
    raise RuntimeError(
        f"Only {len(response.data)} of {len(sightings)} inserted sightings are visible. "
        "Check SELECT permissions and RLS before running this script again."
    )
print(f"Verified {len(response.data)} sightings.")