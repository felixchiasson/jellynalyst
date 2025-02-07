import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..api.jellyseerr import JellyseerrClient
from ..services.requests import RequestService
from ..config import Settings
from ..database.dependencies import init_session_maker

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

   # init_session_maker(session_maker)

    while True:
        try:
            logger.info("Syncing Jellyseerr requests...")

            async with session_maker() as session:
                request_service = RequestService(session)
                # Fetch all requests from Jellyseerr
                requests = await client.get_all_requests()
                logger.info(f"Fetched {len(requests)} requests from Jellyseerr")

                # Sync to database
                await request_service.sync_requests(requests)
                logger.info("Sync complete")

        except Exception as e:
            logger.error(f"Error syncing requests: {e}")

        await asyncio.sleep(interval_seconds)
