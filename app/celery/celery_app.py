from celery import Celery
from kombu import Queue

from app.core.config import settings

app = Celery(
    "elden_rag",
    broker=settings.redis_url,
    include=["app.celery.tasks"],
)

app.conf.update(
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_ignore_result=True,
    task_time_limit=120,
    task_soft_time_limit=90,
    task_routes={
        "app.celery.tasks.discover_category": {"queue": "discovery"},
        "app.celery.tasks.scrape_page": {"queue": "scraping"},
    },
    task_queues=(
        Queue("discovery"),
        Queue("scraping"),
    ),
)
