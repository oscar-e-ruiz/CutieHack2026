import tomllib
import uuid
from datetime import datetime, timezone

from supabase import create_client

with open(".streamlit/secrets.toml", "rb") as file:
    settings = tomllib.load(file)["supabase"]

client = create_client(settings["SUPABASE_URL"], settings["SUPABASE_KEY"])

sighting = {
    "user_id": str(uuid.uuid4()),  # Generates a random valid UUID
    "photo_url": "https://example.com/test-photo.jpg",
    "captured_at": datetime.now(timezone.utc).isoformat(),
    "latitude": 33.97,
    "longitude": -117.33,
}

client.table("Sightings").insert(sighting, returning="minimal").execute()
print("Test sighting inserted!")

response = (
    client.table("Sightings")
    .select("*")
    .eq("user_id", sighting["user_id"])
    .execute()
)

if response.data:
    print("Matching sightings:", response.data)
else:
    print("No matching sighting is visible. Check SELECT permissions and RLS.")