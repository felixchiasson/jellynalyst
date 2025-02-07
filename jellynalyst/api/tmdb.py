from typing import Dict, Any
import httpx
from datetime import datetime
import zoneinfo

class TMDBClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.themoviedb.org/3"

    async def get_media_details(self, media_id: int, media_type: str) -> Dict[str, Any]:
        """
        Get media details from TMDB for a movie or tv show
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/{media_type}/{media_id}",
                params={"api_key": self.api_key}
            )
            response.raise_for_status()
            data = response.json()

            return {
                "id": data["id"],
                "title": data.get("title") or data.get("name"),  # movies use title, TV shows use name
                "original_title": data.get("original_title") or data.get("original_name"),
                "media_type": media_type,
                "genres": [genre["name"] for genre in data.get("genres", [])],
                "overview": data.get("overview"),
                "release_date": datetime.strptime(
                    data.get("release_date") or data.get("first_air_date"),
                    "%Y-%m-%d"
                ).replace(tzinfo=zoneinfo.ZoneInfo("UTC")) if (data.get("release_date") or data.get("first_air_date")) else None,
                "poster_path": data.get("poster_path"),
                "vote_average": data.get("vote_average"),
                "last_updated": datetime.now(zoneinfo.ZoneInfo("UTC"))
            }
