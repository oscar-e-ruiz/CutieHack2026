from dataclasses import dataclass
from datetime import datetime

@dataclass
class User:
    
    id: str
    display_name: str
    profile_photo_url: str | None
    score: int = 0

@dataclass
class Sighting:
    
    id: str
    user_id: str
    photo_url: str
    captured_at: datetime
    submitted_at: datetime
    latitude: float
    longitude: float
    gps_accuracy: float
    group_size: int
    behavior: str
    points_earned: int
