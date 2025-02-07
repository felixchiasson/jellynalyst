from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
import logging

from ..api.jellyfin import JellyfinClient, JellyfinUser, JellyfinWatchItem
from ..database import JellyfinUsers, JellyfinWatchHistory
from ..services.tmdb import TMDBService

logger = logging.getLogger(__name__)

class JellyfinService:
    def __init__(self, session: AsyncSession,
        jellyfin_client: JellyfinClient,
        tmdb_service: TMDBService):
            self.session = session
            self.client = jellyfin_client
            self.tmdb_service = tmdb_service

    async def sync_users(self) -> None:
        """
        Sync users from Jellyfin to the database
        """
        try:
            logger.debug("Getting users from Jellyfin client...")
            jellyfin_users = await self.client.get_users()
            logger.info(f"Fetched {len(jellyfin_users)} users from Jellyfin")

            # Process each user
            for user in jellyfin_users:
                logger.debug(f"Upserting user: {user.username}")
                await self._upsert_user(user)

            # Commit the transaction
            logger.debug("Committing transaction...")
            await self.session.commit()
            logger.info("Sync complete")

        except Exception as e:
            logger.error(f"Error syncing users: {e}")
            raise

    async def _upsert_user(self, user: JellyfinUser) -> None:
        """
        Insert or update a user in the database
        """
        try:
            user_data = {
                "jellyfin_id": user.jellyfin_id,
                "username": user.username,
                "is_administrator": user.is_administrator,
                "primary_image_tag": user.primary_image_tag,
                "last_login": user.last_login,
                "last_seen": user.last_seen
            }
            logger.debug(f"Preparing upsert for user: {user_data['username']}")

            stmt = insert(JellyfinUsers).values(**user_data)
            stmt = stmt.on_conflict_do_update(
                index_elements=["jellyfin_id"],
                set_=user_data
            )

            logger.debug("Executing upsert...")
            await self.session.execute(stmt)
            logger.debug(f"Upsert complete for user: {user_data['username']}")

        except Exception as e:
            logger.error(f"Error upserting user {user.username}: {e}", exc_info=True)
            raise

    async def sync_user_watch_history(self, user_id: str) -> None:
        """
        Sync watch history for a specific user
        """
        try:
            logger.debug(f"Getting watch history for user {user_id}")
            watch_items = await self.client.get_watch_history(user_id)
            logger.info(f"Fetched {len(watch_items)} watch history items for user {user_id}")

            for item in watch_items:
                await self._upsert_watch_history(user_id, item)

            await self.session.commit()
            logger.info(f"Watch history sync complete for user {user_id}")

        except Exception as e:
            logger.error(f"Error syncing watch history for user {user_id}: {e}")
            raise

    async def _upsert_watch_history(self, user_id: str, item: JellyfinWatchItem) -> None:
        """
        Insert or update a watch history item
        """
        if item.last_played_date is None:
            logger.debug(f"Skipping item {item.item_name} - missing last_played_date")
            return

        if item.tmdb_id:
            try:
                # Get or fetch TMDB data
                await self.tmdb_service.get_or_fetch_media(
                    item.tmdb_id,
                    "movie" if item.item_type.lower() == "movie" else "tv"
                )
                logger.debug(f"Retrieved TMDB info for {item.item_name}")
            except Exception as e:
                logger.warning(f"Failed to fetch TMDB data for {item.item_name}: {e}")
                # If we can't get TMDB data, set tmdb_id to None
                item.tmdb_id = None

        try:
            watch_data = {
                "user_id": user_id,
                "item_id": item.item_id,
                "item_name": item.item_name,
                "item_type": item.item_type,
                "tmdb_id": item.tmdb_id,
                "imdb_id": item.imdb_id,
                "genres": item.genres or [],
                "played_percentage": item.played_percentage,
                "play_count": item.play_count,
                "last_played_date": item.last_played_date,
                "is_played": item.is_played,
                "runtime_ticks": item.runtime_ticks,
                "production_year": item.production_year,
            }

            stmt = insert(JellyfinWatchHistory).values(**watch_data)
            stmt = stmt.on_conflict_do_update(
                constraint='uq_user_item',
                set_=watch_data
            )

            await self.session.execute(stmt)
            logger.debug(f"Upserted watch history for item: {item.item_name}")

        except Exception as e:
            logger.error(f"Error upserting watch history for item {item.item_name}: {e}")
            raise
