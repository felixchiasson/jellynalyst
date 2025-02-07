from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta

from ..database import TMDBMedia
from ..api.tmdb import TMDBClient

class TMDBService:
    def __init__(self, session: AsyncSession, tmdb_client: TMDBClient):
        self.session = session
        self.client = tmdb_client

    async def get_or_fetch_media(self, tmdb_id: int, media_type: str) -> TMDBMedia:
        """
        Get media from db or try to fetch from TMDB
        """
        # Check if media exists in db
        result = await self.session.execute(
            select(TMDBMedia).where(TMDBMedia.id == tmdb_id)
        )
        media = result.scalar_one_or_none()

        # If not found or outdated, fetch from TMDB
        # TODO: Add a check for outdated media
        if not media or (
            datetime.now(media.last_updated.tzinfo) - media.last_updated > timedelta(days=7)
        ):
            data = await self.client.get_media_details(tmdb_id, media_type)

            if media:
                for key, value in data.items():
                    setattr(media, key, value)

            else:
                media = TMDBMedia(**data)
                self.session.add(media)

            await self.session.commit()

        return media
