from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import List
from pydantic import BaseModel
import logging

from ..database.models import MediaRequest
from ..database.dependencies import get_session

logger = logging.getLogger("jellynalyst.routes.debug")

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
    request: Request,  # Add this parameter
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

@router.get("/test-logging")
async def test_logging():
    """Test that logging is working"""
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    return {"message": "Logging test complete"}
