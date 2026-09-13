from pydantic import BaseModel

from app.constants import ScraperCategory


class ScrapedPage(BaseModel):
    run_id: str
    category: ScraperCategory
    url: str
    title: str
    content: str


class DiscoveryResult(BaseModel):
    run_id: str
    category: ScraperCategory
    source_url: str
    depth: int
    links_found: int


class RunStatus(BaseModel):
    run_id: str
    categories: list[ScraperCategory]
    discovered: int
    scraped: int
    failed: int
    pending_tasks: int
    complete: bool
