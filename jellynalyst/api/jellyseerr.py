from typing import List, Any, Optional
import httpx
from pydantic import BaseModel, Field
from datetime import datetime
from enum import IntEnum

# Media characteristics
class MediaInfo(BaseModel):
    id: int
    mediaType: str
    tmdbId: int
    status: int
    serviceUrl: Optional[str] = None
    downloadStatus: List[Any] = Field(default_factory=list)

class RequestStatus(IntEnum):
    PENDING = 1
    APPROVED = 2
    AVAILABLE = 3
    DECLINED = 4
    DELETED = 5  # Added for our tracking purposes

    @property
    def display_name(self) -> str:
        return self.name.lower()

# Requestor information
class UserInfo(BaseModel):
    id: int
    email: str
    jellyfinUsername: Optional[str] = None
    displayName: str
    requestCount: int
    jellyfinUserId: Optional[str] = None

class JellyseerrRequest(BaseModel):
    """Model for Jellyseerr get response"""
    id: int
    status: RequestStatus
    createdAt: datetime
    updatedAt: datetime
    type: str
    is4k: bool
    media: MediaInfo
    requestedBy: UserInfo
    modifiedBy: UserInfo
    profileName: Optional[str] = None
    seasonCount: Optional[int] = None

    class Config:
            extra = "allow"

class PageInfo(BaseModel):
    pages: int
    pageSize: int
    results: int
    page: int

class RequestsResponse(BaseModel):
    pageInfo: Optional[PageInfo] = None
    results: List[JellyseerrRequest]

    class Config:
            extra = "allow"

class JellyseerrClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = {"X-Api-Key": api_key}

    async def get_requests(self, page: int = 1, take: int = 100) -> RequestsResponse:
        """Get one page of requests from Jellyseerr"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/request",
                headers=self.api_key,
                params={"take": take, "skip": (page - 1) * take}
            )
            response.raise_for_status()
            return RequestsResponse(**response.json())

    async def get_all_requests(self) -> List[JellyseerrRequest]:
        """
        Get all requests from Jellyseerr
        """
        all_requests = []
        page = 1
        while True:
            response = await self.get_requests(page=page)
            all_requests.extend(response.results)

            # Check if we have more pages
            if not response.pageInfo or page >= response.pageInfo.pages:
                break

            page += 1

        return all_requests

    # Test script
async def test_jellyseerr_client():
    from jellynalyst.config import Settings
    settings = Settings()

    client = JellyseerrClient(
        base_url=settings.JELLYSEERR_URL,
        api_key=settings.JELLYSEERR_API_KEY
    )

    try:
        # Get first page of requests
        response = await client.get_requests(page=1)
        print(f"Page info: {response.pageInfo}")

        if response.results:
            first_request = response.results[0]
            print("\nExample request:")
            print(f"ID: {first_request.id}")
            print(f"Type: {first_request.type}")
            print(f"Status: {first_request.status.display_name}")
            print(f"Requested by: {first_request.requestedBy.displayName}")
            print(f"TMDB ID: {first_request.media.tmdbId}")
            print(f"Created at: {first_request.createdAt}")
            if first_request.seasonCount is not None:
                print(f"Season count: {first_request.seasonCount}")

        # Test getting all requests
        all_requests = await client.get_all_requests()
        print(f"\nFetched all {len(all_requests)} requests successfully")

        # Show status distribution
        status_counts = {}
        for request in all_requests:
            status_counts[request.status.display_name] = status_counts.get(request.status.display_name, 0) + 1

        print("\nStatus distribution:")
        for status, count in status_counts.items():
            print(f"{status}: {count}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_jellyseerr_client())
