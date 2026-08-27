import json
import logging
import os
from urllib.parse import quote

import redis
from django.conf import settings

logger = logging.getLogger(__name__)

REDIS_HOST = getattr(settings, 'REDIS_HOST', os.getenv('REDIS_HOST', 'localhost'))
REDIS_PORT = getattr(settings, 'REDIS_PORT', int(os.getenv('REDIS_PORT', '6379')))
REDIS_PASSWORD = getattr(settings, 'REDIS_PASSWORD', os.getenv('REDIS_PASSWORD', ''))
REDIS_DB = getattr(settings, 'REDIS_DB', int(os.getenv('REDIS_DB', '0')))


def _build_redis_url(host: str, port: int, password: str, db: int) -> str:
    if password:
        return f"redis://:{quote(password, safe='')}@{host}:{port}/{db}"
    return f"redis://{host}:{port}/{db}"


REDIS_URL = getattr(settings, 'REDIS_URL', os.getenv('REDIS_URL', _build_redis_url(REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB)))

r_client = redis.Redis.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
    health_check_interval=30,
    protocol=2,
)

ACTIVE_JOB_KEY = "scraper:active_job_id"
SCRAPER_CONTROL_KEY = "scraper:control:{job_id}"
SCRAPER_CONTROL_CHANNEL = "scraper:control"
LOG_CHANNEL = "scraper:logs:{job_id}"


def check_redis_connection():
    """Pings Redis server, logs host/port/password presence, and raises if unavailable."""
    logger.info(
        "Redis configuration: host=%s port=%s password_configured=%s db=%s",
        REDIS_HOST,
        REDIS_PORT,
        bool(REDIS_PASSWORD),
        REDIS_DB,
    )

    try:
        r_client.ping()
        logger.info("Redis ping: SUCCESS")
        return True
    except redis.exceptions.AuthenticationError as exc:
        logger.error("Redis authentication failed: %s", exc)
        raise
    except redis.exceptions.ConnectionError as exc:
        logger.error("Cannot connect to Redis at %s:%s: %s", REDIS_HOST, REDIS_PORT, exc)
        raise
    except redis.exceptions.RedisError as exc:
        logger.error("Redis ping failed: %s", exc)
        raise


def get_redis_client():
    return r_client


def publish_log(job_id: int, level: str, message: str, page: int = None, company: str = None):
    payload = json.dumps({
        "job_id": job_id,
        "level": level,
        "message": message,
        "page": page,
        "company": company,
    })
    try:
        r_client.publish(LOG_CHANNEL.format(job_id=job_id), payload)
        r_client.publish("scraper:logs:all", payload)
    except redis.RedisError as exc:
        logger.warning("Redis not available for publish_log: %s", exc)


def set_active_job(job_id: int):
    try:
        if job_id is None:
            r_client.delete(ACTIVE_JOB_KEY)
        else:
            r_client.set(ACTIVE_JOB_KEY, str(job_id))
    except redis.RedisError as exc:
        logger.warning("Redis not available for set_active_job: %s", exc)


def clear_active_job():
    try:
        r_client.delete(ACTIVE_JOB_KEY)
    except redis.RedisError as exc:
        logger.warning("Redis not available for clear_active_job: %s", exc)


def get_active_job_id() -> int:
    try:
        val = r_client.get(ACTIVE_JOB_KEY)
        return int(val) if val else None
    except redis.RedisError as exc:
        logger.warning("Redis not available for get_active_job_id: %s", exc)
        return None


def set_scraper_control(job_id: int, command: str):
    control_key = SCRAPER_CONTROL_KEY.format(job_id=job_id)
    try:
        r_client.set(control_key, command, ex=3600)
        payload = json.dumps({"job_id": job_id, "action": command})
        r_client.publish(SCRAPER_CONTROL_CHANNEL, payload)
    except redis.RedisError as exc:
        logger.warning("Failed to publish scraper control command for job %s: %s", job_id, exc)


def get_scraper_control(job_id: int) -> str:
    try:
        return r_client.get(SCRAPER_CONTROL_KEY.format(job_id=job_id))
    except redis.RedisError as exc:
        logger.warning("Redis not available for get_scraper_control: %s", exc)
        return None


def publish_scraper_dispatch(job_payload: dict):
    """Publish scraper dispatch event to Redis channel 'scraper:dispatch'."""
    payload_str = json.dumps(job_payload)
    logger.info("Publishing dispatch event to Redis channel 'scraper:dispatch': %s", payload_str)
    try:
        r_client.publish("scraper:dispatch", payload_str)
    except redis.RedisError as exc:
        logger.warning("Redis not available for publish_scraper_dispatch: %s", exc)


