from dataclasses import dataclass


@dataclass
class User:
    id: str
    display_name: str
    profile_photo_url: str | None
    score: int = 0