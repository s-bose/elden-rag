from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel

from app.constants import ScraperCategory


class PageStatus(StrEnum):
    discovered = "discovered"
    scraped = "scraped"
    failed = "failed"
    embedded = "embedded"


class PageRow(BaseModel):
    id: UUID
    run_id: UUID
    category: ScraperCategory
    url: str
    status: PageStatus
    title: str | None
    content: str | None
    content_hash: str | None
    discovered_at: datetime
    scraped_at: datetime | None


class ChunkRow(BaseModel):
    id: UUID
    page_id: UUID
    heading: str | None
    content: str
    embedding: list[float]
    created_at: datetime
