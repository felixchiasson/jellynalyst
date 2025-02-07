from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from datetime import datetime
from typing import List
from pydantic import BaseModel
import httpx
import logging

from ..database.dependencies import get_session
from ..database.models import TMDBMedia, MediaRequest, JellyfinUsers, JellyfinWatchHistory
from ..api.jellyfin import JellyfinClient
from ..services.jellyfin import JellyfinService
from ..services.tmdb import TMDBClient, TMDBService
from ..config import Settings, get_settings

logger = logging.getLogger("jellynalyst.routes.debug")

class DebugWatchHistoryItem(BaseModel):
    """Model for debug watch history response"""
    id: int
    user_id: str
    item_id: str
    item_type: str
    item_name: str
    tmdb_id: int | None
    imdb_id: str | None
    played_percentage: float | None
    play_count: int
    last_played_date: datetime
    is_played: bool
    runtime_ticks: int | None
    production_year: int | None

class DebugRequest(BaseModel):
    id: int
    jellyseerr_id: int
    tmdb_id: int
    title: str
    media_type: str
    status: str
    request_date: datetime
    requester: str
    genres: List[str]
    is_deleted: bool
    last_checked: datetime

router = APIRouter(prefix="/debug")

def get_jellyfin_client(settings: Settings = Depends(get_settings)) -> JellyfinClient:
    return JellyfinClient(
        base_url=settings.JELLYFIN_URL,
        api_key=settings.JELLYFIN_API_KEY
    )

@router.get("/simple-test")
async def simple_test(session: AsyncSession = Depends(get_session)):
    """Super simple test endpoint"""
    print("=== Simple test endpoint called ===")
    logger.debug("Debug log from simple test")

    try:
        result = await session.execute(select(MediaRequest))
        requests = result.scalars().all()
        count = len(list(requests))
        print(f"Found {count} requests")
        return {"message": "Test endpoint", "count": count}
    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e)}

@router.get("/raw-requests")
async def get_raw_requests(
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    """Most basic debug endpoint to see raw data"""
    logger.debug("=== Starting raw-requests endpoint ===")
    client_host = request.client.host if request.client else "unknown"
    logger.debug(f"Endpoint accessed from: {client_host}")

    try:
        logger.debug("Executing database query...")
        result = await session.execute(select(MediaRequest))
        requests = result.scalars().all()
        logger.info(f"Found {len(requests)} requests in database")

        debug_data = []
        logger.debug("Starting to process requests...")

        for req in requests:
            logger.debug(f"Raw database record: {vars(req)}")

        for req in requests:
            logger.debug(f"Processing request with ID: {getattr(req, 'id', 'unknown')}")
            try:
                logger.debug("Accessing individual fields...")

                id_val = req.id
                logger.debug(f"ID: {id_val}")

                jellyseerr_id = req.jellyseerr_id
                logger.debug(f"Jellyseerr ID: {jellyseerr_id}")

                status = req.status.value if req.status else None
                logger.debug(f"Status: {status}")

                data = {
                    "id": id_val,
                    "jellyseerr_id": jellyseerr_id,
                    "tmdb_id": req.tmdb_id,
                    "title": req.title,
                    "media_type": req.media_type,
                    "status": status,
                    "request_date": req.request_date.isoformat() if req.request_date else None,
                    "requester": req.requester,
                    "genres": req.genres,
                    "is_deleted": req.is_deleted,
                    "last_checked": req.last_checked.isoformat() if req.last_checked else None,
                }
                logger.debug(f"Created data dictionary: {data}")
                debug_data.append(data)
                logger.debug(f"Successfully processed request {id_val}")

            except Exception as e:
                logger.error(f"Problem request data: {vars(req)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Error processing request: {str(e)}"
                )

        logger.debug("Finished processing all requests")
        response_data = {
            "count": len(debug_data),
            "requests": debug_data
        }
        logger.debug("Preparing to return response")
        logger.debug(f"Response data: {response_data}")
        return response_data

    except Exception as e:
        logger.error("Error in raw-requests endpoint:", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )

@router.get("/debug-field")
async def debug_field(
    session: AsyncSession = Depends(get_session)
):
    """Debug specific fields"""
    result = await session.execute(select(MediaRequest))
    requests = result.scalars().all()

    field_debug = []
    for req in requests:
        try:
            field_debug.append({
                "id": req.id,
                "genres_type": type(req.genres).__name__,
                "genres_value": req.genres,
                "status_type": type(req.status).__name__,
                "status_value": req.status.value if req.status else None,
                "dates": {
                    "request_date_type": type(req.request_date).__name__,
                    "request_date": str(req.request_date),
                    "last_checked_type": type(req.last_checked).__name__,
                    "last_checked": str(req.last_checked)
                }
            })
        except Exception as e:
            logger.error(f"Error debugging fields for request {req.id}: {e}")

    return field_debug

@router.get("/jellyfin-users")
async def get_jellyfin_users(
    session: AsyncSession = Depends(get_session)
):
    """Debug endpoint to view Jellyfin users"""
    try:
        result = await session.execute(select(JellyfinUsers))
        users = result.scalars().all()
        return {
            "count": len(users),
            "users": [
                {
                    "id": user.id,
                    "jellyfin_id": user.jellyfin_id,
                    "username": user.username,
                    "is_administrator": user.is_administrator,
                    "last_login": user.last_login.isoformat(),
                    "last_seen": user.last_seen.isoformat()
                }
                for user in users
            ]
        }
    except Exception as e:
        logger.error(f"Error getting Jellyfin users: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching users: {str(e)}"
        )

@router.get("/watch-history/{user_id}", response_model=List[DebugWatchHistoryItem])
async def get_user_watch_history(
    user_id: str,
    limit: int = 50,
    session: AsyncSession = Depends(get_session)
):
    """Get watch history for a specific user"""
    try:
        # First verify the user exists
        logger.debug(f"Looking up user with ID: {user_id}")
        result = await session.execute(
            select(JellyfinUsers)
            .where(JellyfinUsers.jellyfin_id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"User {user_id} not found"
            )

        logger.debug(f"Found user: {user.username}")

        # Debug: Check all unique user_ids in watch_history
        user_query = select(JellyfinWatchHistory.user_id).distinct()
        user_result = await session.execute(user_query)
        unique_users = user_result.scalars().all()
        logger.debug(f"Unique user_ids in watch_history: {unique_users}")

        # Debug: Get a sample record
        sample_query = select(JellyfinWatchHistory).limit(1)
        sample_result = await session.execute(sample_query)
        sample = sample_result.scalar_one_or_none()
        if sample:
            logger.debug(f"Sample record user_id: {sample.user_id}")
            logger.debug(f"Sample record type: {type(sample.user_id)}")
            logger.debug(f"Looking for user_id type: {type(user_id)}")

        # Get watch history
        query = (
            select(JellyfinWatchHistory)
            .where(JellyfinWatchHistory.user_id == user_id)
            .order_by(JellyfinWatchHistory.last_played_date.desc())
            .limit(limit)
        )

        logger.debug(f"Executing query: {query}")

        result = await session.execute(query)
        history = result.scalars().all()

        logger.debug(f"Found {len(history)} watch history items for user {user.username}")

        return [
            DebugWatchHistoryItem(
                id=item.id,
                user_id=item.user_id,
                item_id=item.item_id,
                item_type=item.item_type,
                item_name=item.item_name,
                tmdb_id=item.tmdb_id,
                imdb_id=item.imdb_id,
                played_percentage=item.played_percentage,
                play_count=item.play_count,
                last_played_date=item.last_played_date,
                is_played=item.is_played,
                runtime_ticks=item.runtime_ticks,
                production_year=item.production_year
            )
            for item in history
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting watch history: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching watch history: {str(e)}"
        )

@router.get("/genre-stats/{user_id}")
async def get_user_genre_stats(
    user_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get genre statistics for a user"""
    try:
        # First verify the user exists
        result = await session.execute(
            select(JellyfinUsers)
            .where(JellyfinUsers.jellyfin_id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"User {user_id} not found"
            )

        # Get all genres for this user
        result = await session.execute(
            text("""
            SELECT unnest(genres) as genre, COUNT(*) as count
            FROM watch_history
            WHERE user_id = :user_id
            GROUP BY genre
            ORDER BY count DESC
            """),
            {"user_id": user_id}
        )
        genre_counts = [{"genre": row[0], "count": row[1]} for row in result]

        # Get genre distribution by type
        result = await session.execute(
            text("""
            SELECT item_type, unnest(genres) as genre, COUNT(*) as count
            FROM watch_history
            WHERE user_id = :user_id
            GROUP BY item_type, genre
            ORDER BY item_type, count DESC
            """),
            {"user_id": user_id}
        )
        type_genre_counts = {}
        for row in result:
            item_type = row[0]
            if item_type not in type_genre_counts:
                type_genre_counts[item_type] = []
            type_genre_counts[item_type].append({
                "genre": row[1],
                "count": row[2]
            })

        return {
            "user": {
                "id": user.jellyfin_id,
                "username": user.username
            },
            "overall_genre_counts": genre_counts,
            "genre_counts_by_type": type_genre_counts
        }

    except Exception as e:
        logger.error(f"Error getting genre stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.post("/force-sync-watch-history")
async def force_sync_watch_history(
    session: AsyncSession = Depends(get_session),
    client: JellyfinClient = Depends(get_jellyfin_client)
):
    """Force an immediate sync of watch history"""
    try:
        users = await client.get_users()
        logger.info(f"Found {len(users)} users to process")

        tmdb_client = TMDBClient(api_key=get_settings().TMDB_API_KEY)
        tmdb_service = TMDBService(session, tmdb_client)

        total_synced = 0
        for user in users:
            logger.info(f"Processing user: {user.username}")

            jellyfin_service = JellyfinService(session, client, tmdb_service)
            watch_items = await client.get_watch_history(user.jellyfin_id)
            logger.info(f"Found {len(watch_items)} items for user {user.username}")

            for item in watch_items:
                try:
                    await jellyfin_service._upsert_watch_history(user.jellyfin_id, item)
                    total_synced += 1
                except Exception as e:
                    logger.error(f"Error upserting item {item.item_name}: {e}", exc_info=True)
                    continue

            await session.commit()
            logger.info(f"Completed sync for user {user.username}")

        return {
            "message": "Force sync complete",
            "users_processed": len(users),
            "items_synced": total_synced
        }

    except Exception as e:
        logger.error(f"Error during force sync: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/top-genres")
async def get_top_genres(
    session: AsyncSession = Depends(get_session)
):
    """Get top genres across all users"""
    try:
        # Get overall top genres
        result = await session.execute(
            text("""
            SELECT unnest(genres) as genre, COUNT(*) as count
            FROM watch_history
            GROUP BY genre
            ORDER BY count DESC
            """)
        )
        overall_counts = [{"genre": row[0], "count": row[1]} for row in result]

        # Get top genres by user
        result = await session.execute(
            text("""
            WITH user_genres AS (
                SELECT
                    user_id,
                    unnest(genres) as genre,
                    COUNT(*) as count
                FROM watch_history
                GROUP BY user_id, genre
            )
            SELECT
                u.username,
                ug.genre,
                ug.count
            FROM user_genres ug
            JOIN jellyfin_users u ON u.jellyfin_id = ug.user_id
            ORDER BY u.username, ug.count DESC
            """)
        )

        user_genres = {}
        for row in result:
            username = row[0]
            if username not in user_genres:
                user_genres[username] = []
            user_genres[username].append({
                "genre": row[1],
                "count": row[2]
            })

        return {
            "overall_top_genres": overall_counts,
            "user_top_genres": user_genres
        }

    except Exception as e:
        logger.error(f"Error getting top genres: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/watch-history/genres/{user_id}")
async def get_user_watch_history_genres(
    user_id: str,
    limit: int = 50,
    session: AsyncSession = Depends(get_session)
):
    """Get watch history with genres for a specific user"""
    try:
        # First verify the user exists
        result = await session.execute(
            select(JellyfinUsers)
            .where(JellyfinUsers.jellyfin_id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"User {user_id} not found"
            )

        # Get watch history with genres
        result = await session.execute(
            select(JellyfinWatchHistory)
            .where(JellyfinWatchHistory.user_id == user_id)
            .order_by(JellyfinWatchHistory.last_played_date.desc())
            .limit(limit)
        )
        history = result.scalars().all()

        return {
            "user": {
                "id": user.jellyfin_id,
                "username": user.username
            },
            "count": len(history),
            "history": [
                {
                    "item_name": item.item_name,
                    "item_type": item.item_type,
                    "genres": item.genres,
                    "last_played_date": item.last_played_date.isoformat()
                }
                for item in history
            ]
        }

    except Exception as e:
        logger.error(f"Error getting watch history genres: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/provider-ids/{user_id}")
async def get_provider_ids(
    user_id: str,
    limit: int = 50,
    client: JellyfinClient = Depends(get_jellyfin_client)
):
    """Debug endpoint to examine provider IDs from Jellyfin items"""
    try:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(
                f"{client.base_url}/Users/{user_id}/Items",
                headers=client.headers,
                params={
                    "SortBy": "DatePlayed",
                    "SortOrder": "Descending",
                    "IncludeItemTypes": "Movie,Episode",
                    "Recursive": "true",
                    "Fields": "DateCreated,Path,Genres,MediaStreams,Overview,ProviderIds,UserData"
                }
            )
            response.raise_for_status()
            data = response.json()

            provider_info = []
            for item in data.get("Items", [])[:limit]:
                provider_info.append({
                    "name": item["Name"],
                    "type": item["Type"],
                    "provider_ids": item.get("ProviderIds", {}),
                    "path": item.get("Path", ""),
                    "genres": item.get("Genres", [])
                    # Include path for additional context
                })

            return {
                "total_items": len(data.get("Items", [])),
                "showing": len(provider_info),
                "provider_info": provider_info
            }

    except Exception as e:
        logger.error(f"Error getting provider IDs: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/check-watch-history")
async def check_watch_history(
    session: AsyncSession = Depends(get_session)
):
    """Debug endpoint to check watch history table"""
    try:
        # Get total count
        count_query = select(func.count()).select_from(JellyfinWatchHistory)
        count_result = await session.execute(count_query)
        total_count = count_result.scalar()

        # Get sample records
        sample_query = select(JellyfinWatchHistory).limit(5)
        sample_result = await session.execute(sample_query)
        samples = sample_result.scalars().all()

        return {
            "total_records": total_count,
            "table_name": JellyfinWatchHistory.__tablename__,
            "sample_records": [
                {
                    "id": item.id,
                    "user_id": item.user_id,
                    "item_id": item.item_id,
                    "item_name": item.item_name,
                    "last_played_date": item.last_played_date.isoformat()
                }
                for item in samples
            ]
        }
    except Exception as e:
        logger.error(f"Error checking watch history table: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/requests", response_model=List[DebugRequest])
async def get_requests(
    limit: int = 10,
    session: AsyncSession = Depends(get_session)
):
    """Debug endpoint to view recent requests"""
    try:
        result = await session.execute(
            select(MediaRequest)
            .order_by(MediaRequest.request_date.desc())
            .limit(limit)
        )
        requests = result.scalars().all()

        response_data = []
        for req in requests:
            try:
                item = DebugRequest(
                    id=req.id,
                    jellyseerr_id=req.jellyseerr_id,
                    tmdb_id=req.tmdb_id,
                    title=req.title,
                    media_type=req.media_type,
                    status=req.status.value,
                    request_date=req.request_date,
                    requester=req.requester,
                    genres=req.genres or [],  # Ensure it's never None
                    is_deleted=req.is_deleted,
                    last_checked=req.last_checked
                )
                response_data.append(item)
            except Exception as e:
                logger.error(f"Error processing request {req.id} for response: {e}")
                logger.error(f"Request data: {req.__dict__}")

        return response_data

    except Exception as e:
        logger.error(f"Error in get_requests: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching requests: {str(e)}"
        )

@router.get("/tmdb-stats")
async def get_tmdb_stats(session: AsyncSession = Depends(get_session)):
    """Get statistics about TMDB data"""
    try:
        # Get total count
        result = await session.execute(
            select(TMDBMedia.media_type, func.count().label('count'))
            .group_by(TMDBMedia.media_type)
        )
        counts_by_type = {t: c for t, c in result}

        # Get genre distribution
        result = await session.execute(
            text("""
            SELECT
                unnest(genres) as genre,
                COUNT(*) as count
            FROM tmdb_media
            GROUP BY genre
            ORDER BY count DESC
        """)
        )
        genre_counts = {row[0]: row[1] for row in result}

        # Get recent updates
        result = await session.execute(
            select(TMDBMedia)
            .order_by(TMDBMedia.last_updated.desc())
            .limit(5)
        )
        recent_updates = [
            {
                "id": m.id,
                "title": m.title,
                "media_type": m.media_type,
                "last_updated": m.last_updated.isoformat()
            }
            for m in result.scalars()
        ]

        return {
            "total_items": sum(counts_by_type.values()),
            "counts_by_type": counts_by_type,
            "genre_distribution": genre_counts,
            "recent_updates": recent_updates
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting TMDB stats: {str(e)}"
        )

@router.get("/test-logging")
async def test_logging():
    """Test that logging is working"""
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    return {"message": "Logging test complete"}
