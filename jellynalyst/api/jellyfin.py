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
