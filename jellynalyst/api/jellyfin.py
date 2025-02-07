from typing import List
from pydantic import BaseModel
import httpx
from datetime import datetime
import logging

class JellyfinUser(BaseModel):
    """Model for Jellyfin API response, matching database schema"""
    id: int
    jellyfin_id: str
    username: str
    is_administrator: bool
    primary_image_tag: str | None
    last_login: datetime
    last_seen: datetime

    class Config:
            from_attributes = True

class JellyfinWatchItem(BaseModel):
    """Model for Jellyfin watch history item response"""
    item_id: str
    item_name: str
    item_type: str
    tmdb_id: int | None
    imdb_id: str | None
    genres: List[str] | None
    played_percentage: float | None
    play_count: int
    last_played_date: datetime | None
    is_played: bool
    runtime_ticks: int | None
    production_year: int | None

logger = logging.getLogger(__name__)

class JellyfinClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.headers = {"X-MediaBrowser-Token": api_key}

    async def get_users(self) -> List[JellyfinUser]:
        """Get all users from Jellyfin"""
        logger.debug(f"Making request to Jellyfin API: {self.base_url}/Users")
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/Users",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            logger.debug(f"Raw user data from Jellyfin: {data}")
            users = []
            for user in response.json():
                users.append(JellyfinUser(
                    id=0,  # This will be assigned by the database
                    jellyfin_id=user["Id"],
                    username=user["Name"],
                    is_administrator=user["Policy"]["IsAdministrator"],
                    primary_image_tag=user.get("PrimaryImageTag"),
                    last_login=user.get("LastLoginDate", datetime.utcnow()),
                    last_seen=user.get("LastActivityDate", datetime.utcnow())
                ))
            return users

    async def get_watch_history(self, user_id: str) -> List[JellyfinWatchItem]:
        """
        Get watch history for a user from Jellyfin
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/Users/{user_id}/Items",
                headers=self.headers,
                params={
                    "SortBy": "DatePlayed",
                    "SortOrder": "Descending",
                    "EnableUserData": "true",
                    "IncludeItemTypes": "Movie,Episode",
                    "Recursive": "true",
                    "Fields": "DateCreated,Path,Genres,MediaStreams,Overview,ProviderIds,UserData"
                }
            )
            response.raise_for_status()
            data = response.json()

            watch_items: List[JellyfinWatchItem] = []

            for item in data.get("Items", []):
                # Default values
                tmdb_id = None
                provider_ids = item.get("ProviderIds", {})
                user_data = item.get("UserData", {})

                # Try to get TMDB ID
                if tmdb_str := provider_ids.get("Tmdb"):
                    try:
                        tmdb_id = int(tmdb_str)
                    except (ValueError, TypeError):
                        pass

                watch_item = JellyfinWatchItem(
                    item_id=item["Id"],
                    item_name=item["Name"],
                    item_type=item["Type"],
                    tmdb_id=tmdb_id,
                    imdb_id=provider_ids.get("Imdb"),
                    genres=item.get("Genres", []),
                    played_percentage=user_data.get("PlayedPercentage"),
                    play_count=user_data.get("PlayCount", 0),
                    last_played_date=user_data.get("LastPlayedDate"),
                    is_played=user_data.get("Played", False),
                    runtime_ticks=item.get("RunTimeTicks"),
                    production_year=item.get("ProductionYear")
                )
                watch_items.append(watch_item)

            return watch_items
