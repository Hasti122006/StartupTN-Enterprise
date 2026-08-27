from typing import Any
from celery import shared_task

from .models import Job
from .services.n8n_client import trigger_n8n_scrape_job


def dispatch_scraper_job(job_id: int, extra_payload: dict[str, Any] | None = None) -> str:
    """Send a job to n8n scraper pipeline via HTTP webhook."""
    job = Job.objects.filter(id=job_id).first()
    if not job:
        raise ValueError(f"Job #{job_id} does not exist")

    success, msg = trigger_n8n_scrape_job(job)
    if not success:
        job.status = 'failed'
        job.error_message = msg
        job.save(update_fields=['status', 'error_message', 'updated_at'])
        raise RuntimeError(msg)

    job.status = 'running'
    job.save(update_fields=['status', 'updated_at'])
    return f"Job #{job_id} dispatched to n8n webhook"


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def run_scraper_task(self, job_id: int):
    """Dispatch exactly one existing job to n8n via Celery task."""
    try:
        return dispatch_scraper_job(job_id)
    except Exception as exc:
        job = Job.objects.filter(id=job_id).first()
        if not job:
            return f"Job #{job_id} does not exist"
        job.status = 'failed'
        job.error_message = f"Scraper dispatch failed: {exc}"
        job.save(update_fields=['status', 'error_message', 'updated_at'])
        raise self.retry(exc=exc)
