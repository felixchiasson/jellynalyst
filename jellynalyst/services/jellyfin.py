from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
import logging

from ..api.jellyfin import JellyfinClient, JellyfinUser
from ..database.models import JellyfinUsers

logger = logging.getLogger(__name__)

class JellyfinService:
    def __init__(self, session: AsyncSession,
        jellyfin_client: JellyfinClient):
            self.session = session
            self.client = jellyfin_client

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
