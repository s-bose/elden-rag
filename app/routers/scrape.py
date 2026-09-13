import asyncio
from uuid import UUID

from fastapi import APIRouter, Path, Query
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool

from app.celery.schemas import RunStatus
from app.celery.tasks import get_run_status, start_run
from app.constants import ScraperCategory

router = APIRouter(prefix="/scraper")


@router.post("/enqueue")
def enqueue_scrappers(category: ScraperCategory = Query(ScraperCategory.all)) -> dict[str, str]:
    categories = None if category == ScraperCategory.all else [category]
    run_id = start_run(categories)
    return {"run_id": run_id}


@router.get("/{run_id}")
def get_job_status(run_id: UUID = Path(...)) -> RunStatus:
    return get_run_status(str(run_id))


@router.get("/{run_id}/stream")
async def stream_run_status(run_id: UUID = Path(...)) -> StreamingResponse:
    async def event_source():
        while True:
            status = await run_in_threadpool(get_run_status, str(run_id))
            yield f"data: {status.model_dump_json()}\n\n"
            if status.complete:
                break
            await asyncio.sleep(2)

    return StreamingResponse(event_source(), media_type="text/event-stream")
