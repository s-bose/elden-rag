import uuid

import requests

from app.celery.celery_app import app
from app.celery.helpers import RedisKey
from app.celery.schemas import DiscoveryResult, ScrapedPage
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
        scrape_page.apply_async(args=[run_id, category, link_url])

        if cfg.recursive and depth < cfg.max_depth:
            discover_category.apply_async(args=[run_id, category, link_url, depth + 1])

    return DiscoveryResult(
        run_id=run_id, category=category, source_url=url, depth=depth, links_found=links_found
    )


@app.task(bind=True, max_retries=3, default_retry_delay=30, rate_limit=settings.scraper_rate_limit)
def scrape_page(self, run_id: str, category: ScraperCategory, url: str) -> ScrapedPage | None:
    done_key = RedisKey.DONE(run_id=run_id)
    if redis_client.is_member(done_key, url):
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
            return None

    allow_patterns = CATEGORIES[category].allow_patterns
    content = scraper.parse_page(html, allow_patterns)
    if not content:
        return None

    title = scraper.page_title(html)
    redis_client.add_to_set(done_key, url, ttl=settings.scraper_run_ttl_seconds)

    return ScrapedPage(run_id=run_id, category=category, url=url, title=title, content=content)


def start_run(categories: list[ScraperCategory] | None = None) -> str:
    run_id = str(uuid.uuid4())
    for category in categories or list(CATEGORIES):
        cfg = CATEGORIES[category]
        for seed in cfg.seeds:
            seed_url = settings.scraper_base_url + seed
            discover_category.delay(run_id, category, seed_url, 0)
    return run_id


def requeue_failed(run_id: str) -> int:
    failed_key = RedisKey.FAILED(run_id=run_id)
    entries = redis_client.members(failed_key)
    for entry in entries:
        category_str, url = entry.split("::", 1)
        redis_client.remove_from_set(failed_key, entry)
        scrape_page.apply_async(args=[run_id, ScraperCategory(category_str), url])
    return len(entries)
