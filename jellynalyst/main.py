from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
import asyncio
import logging

# Local imports
from .config import Settings
from .database.models import init_db, get_db, MediaRequest
from .tasks.sync import sync_jellyseerr_requests

app = FastAPI(title="Jellynalyst", version="0.1.0")

logger = logging.getLogger(__name__)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Settings
settings = Settings(_env_file='.env')

# Global variables
session_maker: async_sessionmaker[AsyncSession] | None = None
sync_task = None

@app.on_event("startup")
async def startup_event():
    global session_maker, sync_task

    try:
        # Init database
        logger.info("Initializing database...")
        session_maker = await init_db(settings)
        logger.info("Database initialized")

        # Start sync task
        logger.info("Starting requests sync task...")
        sync_task = asyncio.create_task(
            sync_jellyseerr_requests(
                session_maker=session_maker,
                settings=settings
            )
        )
        sync_task.add_done_callback(handle_sync_task_complete)
        logger.info("Sync task started successfully")

    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

def handle_sync_task_complete(task):
    """Handle the completion of the requests sync task"""
    try:
        task.result()
    except asyncio.CancelledError:
        logger.info("Sync task was cancelled")
    except Exception as e:
        logger.error(f"Sync task failed with error: {e}")

@app.get("/")
async def home():
    return templates.TemplateResponse("index.html", {"request": {}})

@app.get("/api/stats")
async def get_stats(db: AsyncSession = Depends(lambda: get_db(session_maker))):
    return {"message": "TODO: implement stats"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Temporary debug endpoint
@app.get("/debug/requests")
async def get_requests(
    limit: int = 10,
    session: AsyncSession = Depends(get_db)
):
    """Debug endpoint to view recent requests"""
    result = await session.execute(
        select(MediaRequest)
        .order_by(MediaRequest.request_date.desc())
        .limit(limit)
    )
    requests = result.scalars().all()

    return [{
        "id": req.id,
        "jellyseerr_id": req.jellyseerr_id,
        "title": req.title,
        "status": req.status.name,
        "request_date": req.request_date,
        "requester": req.requester,
        "is_deleted": req.is_deleted,
        "last_checked": req.last_checked
    } for req in requests]

@app.on_event("shutdown")
async def shutdown_event():
    global sync_task

    # Cancel sync task
    if sync_task:
        logger.info("Cancelling sync task...")
        sync_task.cancel()
        try:
            await sync_task
        except asyncio.CancelledError:
            logger.info("Sync task cancelled successfully")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=37192)
