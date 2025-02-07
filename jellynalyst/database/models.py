from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, ARRAY, Boolean, Enum, Float, ForeignKey
from datetime import datetime
from typing import List
import enum

class Base(DeclarativeBase):
    pass

class RequestStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    AVAILABLE = "available"
    DECLINED = "declined"
    DELETED = "deleted"
# Jellyfin Users
class JellyfinUsers(Base):
    __tablename__ = "jellyfin_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    jellyfin_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    is_administrator: Mapped[bool] = mapped_column(Boolean, nullable=False)
    # http://192.168.2.100:8096/Users/b7dfa727ca7147e1885785a6aee7c336/Images/Primary?width=600&tag=81ffa2dfed497ae90f0b04bb9f108933&quality=90
    # Could use this somehow
    primary_image_tag: Mapped[str] = mapped_column(String(100), nullable=True)
    last_login: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def __repr__(self) -> str:
        return f"<JellyfinUser(id={self.id}, username={self.username})>"

# TMDB
class TMDBMedia(Base):
    __tablename__ = "tmdb_media"

    id: Mapped[int] = mapped_column(primary_key=True) # media_request.tmdb_id
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    original_title: Mapped[str] = mapped_column(String(255), nullable=True)
    media_type: Mapped[str] = mapped_column(String(50), nullable=False)
    genres: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    overview: Mapped[str] = mapped_column(String, nullable=True) # this is the description
    release_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    poster_path: Mapped[str] = mapped_column(String, nullable=True)
    vote_average: Mapped[float] = mapped_column(Float, nullable=True)
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationship with MediaRequest
    requests: Mapped[List["MediaRequest"]] = relationship("MediaRequest", back_populates="tmdb_info")

class MediaRequest(Base):
    __tablename__ = "media_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    jellyseerr_id: Mapped[int] = mapped_column(unique=True)
    tmdb_id: Mapped[int] = mapped_column(ForeignKey("tmdb_media.id"), nullable=False)
    media_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    request_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[RequestStatus] = mapped_column(Enum(RequestStatus), nullable=False)
    requester: Mapped[str] = mapped_column(String(100), nullable=False)
    genres: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    last_checked: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationship with TMDBMedia
    tmdb_info: Mapped[TMDBMedia] = relationship("TMDBMedia", back_populates="requests")

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
