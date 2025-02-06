from datetime import datetime
from typing import List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
import zoneinfo

from ..api.jellyseerr import JellyseerrRequest, RequestStatus as JellyseerrStatus
from ..database.models import MediaRequest, RequestStatus as DBRequestStatus

class RequestService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def sync_requests(self, jellyseerr_requests: List[JellyseerrRequest]) -> None:
        """
        Sync requests from Jellyseerr to the database
        """
        # Get all existing requests
        existing_ids = await self._get_existing_request_ids()

        # Process each request
        for request in jellyseerr_requests:
            await self._upsert_request(request)

        # Mark requests as deleted if they no longer exist in Jellyseerr
        current_ids = {req.id for req in jellyseerr_requests}
        deleted_ids = existing_ids - current_ids

        if deleted_ids:
            await self._mark_requests_deleted(deleted_ids)

        # Commit the transaction
        await self.session.commit()


    async def _get_existing_request_ids(self) -> set[int]:
        """
        Get all existing request IDs from the database
        """
        result = await self.session.execute(select(MediaRequest.jellyseerr_id))
        return {row[0] for row in result.all()}

    async def _upsert_request(self, request: JellyseerrRequest) -> None:
        """
        Insert or update a request in the database
        """
        status = self._map_status(request.status)

        # Prepare the request data
        request_data = {
            "jellyseerr_id": request.id,
            "tmdb_id": request.media.tmdbId,
            "media_type": request.type,
            "title": request.media.mediaType, # TODO: Fetch tmdb titles
            "request_date": request.createdAt,
            "status": status,
            "requester": request.requestedBy.displayName,
            "genres": [], # TODO: Fetch tmdb genres,
            "is_deleted": False,
            "last_checked": datetime.now(),
        }

        stmt = insert(MediaRequest).values(**request_data)
        stmt = stmt.on_conflict_do_update(
            index_elements=["jellyseerr_id"], set_=request_data
        )

        await self.session.execute(stmt)

    def _map_status(self, jellyseerr_status: JellyseerrStatus) -> DBRequestStatus:
        """Map Jellyseerr status to database status"""
        status_map = {
            JellyseerrStatus.PENDING: DBRequestStatus.PENDING,
            JellyseerrStatus.APPROVED: DBRequestStatus.APPROVED,
            JellyseerrStatus.AVAILABLE: DBRequestStatus.AVAILABLE,
            JellyseerrStatus.DECLINED: DBRequestStatus.DECLINED,
        }
        return status_map.get(jellyseerr_status, DBRequestStatus.PENDING)

    async def _mark_requests_deleted(self, jellyseerr_ids: set[int]) -> None:
        """
        Mark requests as deleted in the database if
        they no longer exist in seerr
        """
        await self.session.execute(
            update(MediaRequest)
            .where(
                MediaRequest
                .jellyseerr_id
                .in_(jellyseerr_ids)
            )
            .values(
                is_deleted=True,
                status=DBRequestStatus.DELETED,
                last_checked=datetime.utcnow()
            )
        )
