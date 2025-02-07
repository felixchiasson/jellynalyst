import logging
from logging.config import dictConfig

logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "DEBUG"
        }
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG"
    },
    "loggers": {
        "jellynalyst": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False
        }
    }
}

dictConfig(logging_config)
logger = logging.getLogger(__name__)

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import asyncio

# Local imports
from .config import Settings
from .database import init_db, init_session_maker
from .tasks.sync import sync_jellyseerr_requests, sync_jellyfin_users
from .routes import router


app = FastAPI(title="Jellynalyst", version="0.1.0")

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Settings
settings = Settings(_env_file='.env')

app.include_router(router)

# Global variables
sync_task = None
sync_users_task = None

@app.on_event("startup")
async def startup_event():
    global sync_task, sync_users_task

    try:
        # Init database
        logger.info("Initializing database...")
        session_maker = await init_db(settings)
        init_session_maker(session_maker)
        logger.info("Database initialized")

        # Start sync task
        logger.info("Starting requests sync task...")
        sync_task = asyncio.create_task(
            sync_jellyseerr_requests(
                session_maker=session_maker,
                settings=settings
            )
        )

        sync_users_task = asyncio.create_task(
            sync_jellyfin_users(
                session_maker=session_maker,
                settings=settings
            )
        )

        sync_task.add_done_callback(handle_sync_task_complete)
        sync_users_task.add_done_callback(handle_sync_task_complete)

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

        if sync_users_task:  # Add this block
            logger.info("Cancelling Jellyfin users sync task...")
            sync_users_task.cancel()
            try:
                await sync_users_task
            except asyncio.CancelledError:
                logger.info("Jellyfin users sync task cancelled successfully")
