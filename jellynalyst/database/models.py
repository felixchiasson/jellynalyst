from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, ARRAY, Boolean
from datetime import datetime
from typing import List
from typing import AsyncGenerator
import enum

class Base(DeclarativeBase):
    pass

class RequestStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    AVAILABLE = "available"
    DECLINED = "declined"
    DELETED = "deleted"

class MediaRequest(Base):
    __tablename__ = "media_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    jellyseerr_id: Mapped[int] = mapped_column(unique=True)
    tmdb_id: Mapped[int] = mapped_column(nullable=False)
    media_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    request_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[RequestStatus] = mapped_column(nullable=False)
    requester: Mapped[str] = mapped_column(String(100), nullable=False)
    genres: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    last_checked: Mapped[datetime] = mapped_column(DateTime, nullable=False)

# Database connection
async def init_db(settings):
    engine = create_async_engine(settings.DATABASE_URL)

    async_session = async_sessionmaker(
            engine,
            expire_on_commit=False,
            class_=AsyncSession
        )

    async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    return async_session

async def get_db(async_session) -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
