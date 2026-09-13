from uuid import UUID
from app.constants import ScraperCategory
from fastapi import APIRouter, Query, Path

router = APIRouter(prefix="/scraper")

@router.post("/enqueue")
async def enqueue_scrappers(
    category: ScraperCategory = Query(ScraperCategory.all),
):
    pass


@router.get("/{job_id:uuid}")
async def get_job_status(job_id: UUID = Path(...)):
    pass
