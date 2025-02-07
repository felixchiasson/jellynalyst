from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from typing import AsyncGenerator

# Global session maker
session_maker: async_sessionmaker[AsyncSession] | None = None

def init_session_maker(new_session_maker: async_sessionmaker[AsyncSession]) -> None:
    """Initialize the global session maker"""
    global session_maker
    session_maker = new_session_maker

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database sessions"""
    if session_maker is None:
        raise RuntimeError("Database session maker not initialized")

    async with session_maker() as session:
        yield session
