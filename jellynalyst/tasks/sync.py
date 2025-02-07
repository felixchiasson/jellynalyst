import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..api.jellyseerr import JellyseerrClient
from ..api.tmdb import TMDBClient
from ..api.jellyfin import JellyfinClient
from ..services.requests import RequestService
from ..services.tmdb import TMDBService
from ..services.jellyfin import JellyfinService
from ..config import Settings

logger = logging.getLogger(__name__)

async def sync_jellyseerr_requests(
    session_maker: async_sessionmaker[AsyncSession],
    settings: Settings,
    interval_seconds: int = 300 # 5 minutes
) -> None:
    """
    Periodically sync requests from Jellyseerr
    """
    client = JellyseerrClient(
        base_url=settings.JELLYSEERR_URL,
        api_key=settings.JELLYSEERR_API_KEY
    )

    tmdb_client = TMDBClient(
            api_key=settings.TMDB_API_KEY
        )

    while True:
        try:
            logger.info("Syncing Jellyseerr requests...")

            async with session_maker() as session:
                tmdb_service = TMDBService(session, tmdb_client)
                request_service = RequestService(session, tmdb_service)
                # Fetch all requests from Jellyseerr
                requests = await client.get_all_requests()
                logger.info(f"Fetched {len(requests)} requests from Jellyseerr")

                # Sync to database
                await request_service.sync_requests(requests)
                logger.info("Sync complete")

        except Exception as e:
            logger.error(f"Error syncing requests: {e}")

        await asyncio.sleep(interval_seconds)

async def sync_jellyfin_users(
    session_maker: async_sessionmaker[AsyncSession],
    settings: Settings,
    interval_seconds: int = 300 # 5 minutes
) -> None:
    """
    Periodically sync users from Jellyfin
    """
    logger.info("Starting Jellyfin users sync task")
    client = JellyfinClient(
        base_url=settings.JELLYFIN_URL,
        api_key=settings.JELLYFIN_API_KEY
    )

    while True:
        try:
            logger.info("Syncing Jellyfin users...")

            async with session_maker() as session:
                jellyfin_service = JellyfinService(session, client)
                # Fetch all users from Jellyfin
                await jellyfin_service.sync_users()

        except Exception as e:
            logger.error(f"Error syncing users: {e}")

        await asyncio.sleep(interval_seconds)
