import uuid

import requests

from app.celery.celery_app import app
from app.celery.helpers import RedisKey
from app.celery.schemas import DiscoveryResult, RunStatus, ScrapedPage
from app.constants import ScraperCategory
from app.core.config import settings
from app.core.redis import redis_client
from app.scraper.fextralife import FextralifeScraper
from app.scraper.seeds import CATEGORIES

scraper = FextralifeScraper()


@app.task(bind=True, max_retries=3, default_retry_delay=30)
def discover_category(
    self, run_id: str, category: ScraperCategory, url: str, depth: int = 0
) -> DiscoveryResult:
    cfg = CATEGORIES[category]
    pending_key = RedisKey.PENDING(run_id=run_id)
    try:
        html = scraper.fetch_html(url)
    except requests.RequestException as exc:
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            failed_key = RedisKey.FAILED(run_id=run_id)
            redis_client.add_to_set(
                failed_key, f"{category}::{url}", ttl=settings.scraper_run_ttl_seconds
            )
            redis_client.decr(pending_key)
            return DiscoveryResult(
                run_id=run_id, category=category, source_url=url, depth=depth, links_found=0
            )

    seen_key = RedisKey.SEEN(run_id=run_id, category=category)
    links_found = 0
    for link_url, _link_text in scraper.extract_links(html, settings.scraper_base_url):
        newly_seen = redis_client.add_to_set(
            seen_key, link_url, ttl=settings.scraper_run_ttl_seconds
        )
        if not newly_seen:
            continue

        links_found += 1
        redis_client.incr(pending_key, ttl=settings.scraper_run_ttl_seconds)
        scrape_page.apply_async(args=[run_id, category, link_url])

        if cfg.recursive and depth < cfg.max_depth:
            redis_client.incr(pending_key, ttl=settings.scraper_run_ttl_seconds)
            discover_category.apply_async(args=[run_id, category, link_url, depth + 1])

    redis_client.decr(pending_key)
    return DiscoveryResult(
        run_id=run_id, category=category, source_url=url, depth=depth, links_found=links_found
    )


@app.task(bind=True, max_retries=3, default_retry_delay=30, rate_limit=settings.scraper_rate_limit)
def scrape_page(self, run_id: str, category: ScraperCategory, url: str) -> ScrapedPage | None:
    done_key = RedisKey.DONE(run_id=run_id)
    pending_key = RedisKey.PENDING(run_id=run_id)
    if redis_client.is_member(done_key, url):
        redis_client.decr(pending_key)
        return None

    try:
        html = scraper.fetch_html(url)
    except requests.RequestException as exc:
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            failed_key = RedisKey.FAILED(run_id=run_id)
            redis_client.add_to_set(
                failed_key, f"{category}::{url}", ttl=settings.scraper_run_ttl_seconds
            )
            redis_client.decr(pending_key)
            return None

    allow_patterns = CATEGORIES[category].allow_patterns
    content = scraper.parse_page(html, allow_patterns)
    if not content:
        redis_client.decr(pending_key)
        return None

    title = scraper.page_title(html)
    redis_client.add_to_set(done_key, url, ttl=settings.scraper_run_ttl_seconds)
    redis_client.decr(pending_key)

    return ScrapedPage(run_id=run_id, category=category, url=url, title=title, content=content)


def start_run(categories: list[ScraperCategory] | None = None) -> str:
    run_id = str(uuid.uuid4())
    categories_key = RedisKey.CATEGORIES(run_id=run_id)
    pending_key = RedisKey.PENDING(run_id=run_id)

    for category in categories or list(CATEGORIES):
        cfg = CATEGORIES[category]
        redis_client.add_to_set(categories_key, category, ttl=settings.scraper_run_ttl_seconds)
        for seed in cfg.seeds:
            seed_url = settings.scraper_base_url + seed
            redis_client.incr(pending_key, ttl=settings.scraper_run_ttl_seconds)
            discover_category.delay(run_id, category, seed_url, 0)

    return run_id


def get_run_status(run_id: str) -> RunStatus:
    categories = sorted(ScraperCategory(c) for c in redis_client.members(
        RedisKey.CATEGORIES(run_id=run_id)
    ))
    discovered = sum(
        len(redis_client.members(RedisKey.SEEN(run_id=run_id, category=c))) for c in categories
    )
    scraped = len(redis_client.members(RedisKey.DONE(run_id=run_id)))
    failed = len(redis_client.members(RedisKey.FAILED(run_id=run_id)))
    pending = redis_client.get_int(RedisKey.PENDING(run_id=run_id))

    return RunStatus(
        run_id=run_id,
        categories=categories,
        discovered=discovered,
        scraped=scraped,
        failed=failed,
        pending_tasks=pending,
        complete=pending <= 0,
    )


def requeue_failed(run_id: str) -> int:
    failed_key = RedisKey.FAILED(run_id=run_id)
    pending_key = RedisKey.PENDING(run_id=run_id)
    entries = redis_client.members(failed_key)
    for entry in entries:
        category_str, url = entry.split("::", 1)
        redis_client.remove_from_set(failed_key, entry)
        redis_client.incr(pending_key, ttl=settings.scraper_run_ttl_seconds)
        scrape_page.apply_async(args=[run_id, ScraperCategory(category_str), url])
    return len(entries)
