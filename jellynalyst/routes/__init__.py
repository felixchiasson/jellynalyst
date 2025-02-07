from fastapi import APIRouter
from .api import router as api_router
from .debug import router as debug_router
from .views import router as views_router

router = APIRouter()
router.include_router(api_router)
router.include_router(debug_router)
router.include_router(views_router)
