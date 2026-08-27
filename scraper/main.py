from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time

import redis as sync_redis

from config import ScraperConfig
from scraper import StartupTNScraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("scraper.main")


def _wait_for_redis(config: ScraperConfig, max_retries: int = 10, delay: float = 3.0) -> sync_redis.Redis:
    """
    Attempt to connect to Redis with retries.
    The scraper container starts alongside Redis; we give Redis time to become ready.
    """
    for attempt in range(1, max_retries + 1):
        try:
            client = sync_redis.from_url(
                config.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
            )
            client.ping()
            logger.info("Redis connection established.")
            return client
        except Exception as exc:
            logger.warning(
                f"Redis not ready (attempt {attempt}/{max_retries}): {exc}. "
                f"Retrying in {delay}s..."
            )
            time.sleep(delay)
    logger.error("Could not connect to Redis after %d attempts. Exiting.", max_retries)
    sys.exit(1)


async def run_single_job(config: ScraperConfig) -> None:
    """Run the scraper once for the job ID set in SCRAPER_JOB_ID."""
    scraper = StartupTNScraper(config)
    await scraper.run()


async def run_daemon(config: ScraperConfig) -> None:
    """
    Run as a persistent daemon: subscribe to Redis channel 'scraper:dispatch'
    and spawn a scraper job for each dispatched message.
    """
    logger.info("No SCRAPER_JOB_ID set — starting in daemon (listener) mode.")
    r = _wait_for_redis(config)
    pubsub = r.pubsub()
    pubsub.subscribe("scraper:dispatch")
    logger.info("Listening on Redis channel 'scraper:dispatch'…")

    for message in pubsub.listen():
        if message.get("type") != "message":
            continue
        try:
            payload = message["data"]
            logger.info(f"Received job dispatch: {payload}")

            try:
                job_data = json.loads(payload)
                job_id = str(job_data.get("job_id", ""))
            except (json.JSONDecodeError, AttributeError):
                job_id = str(payload).strip()

            if job_id:
                os.environ["SCRAPER_JOB_ID"] = job_id
                # The Django job controls apply to this run only; they are not
                # persisted globally in the daemon container.
                for payload_key, env_key in {
                    "start_page": "SCRAPER_START_PAGE",
                    "end_page": "SCRAPER_END_PAGE",
                    "workers": "SCRAPER_WORKERS",
                    "delay_min": "SCRAPER_DELAY_MIN",
                    "delay_max": "SCRAPER_DELAY_MAX",
                    "retry_count": "SCRAPER_RETRY_COUNT",
                    "timeout": "SCRAPER_TIMEOUT",
                    "company_limit": "SCRAPER_COMPANY_LIMIT",
                }.items():
                    if isinstance(job_data, dict) and payload_key in job_data:
                        os.environ[env_key] = str(job_data[payload_key])
                if isinstance(job_data, dict) and "headless" in job_data:
                    os.environ["SCRAPER_HEADLESS"] = str(job_data["headless"]).lower()
                # Re-create config so __post_init__ picks up the new env var
                fresh_config = ScraperConfig()
                scraper = StartupTNScraper(fresh_config)
                try:
                    await scraper.run()
                except Exception as exc:
                    logger.error(f"Scraper job {job_id} failed: {exc}", exc_info=True)
            else:
                logger.warning(f"Dispatch message contained no parseable job_id: {payload!r}")

        except Exception as exc:
            logger.error(f"Error handling dispatch message: {exc}", exc_info=True)


async def main() -> None:
    config = ScraperConfig()

    job_id = os.getenv("SCRAPER_JOB_ID", "").strip()
    if job_id:
        logger.info(f"Launching scraper for Job ID: {job_id}")
        await run_single_job(config)
    else:
        await run_daemon(config)


if __name__ == "__main__":
    asyncio.run(main())
