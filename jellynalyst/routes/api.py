from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session

router = APIRouter()

@router.get("/stats")
async def get_stats(session: AsyncSession = Depends(get_session)):
    #TODO: Implement stats endpoint
    pass
