import logging
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def trigger_n8n_scrape_job(job) -> tuple[bool, str]:
    """Send HTTP POST to N8N_WEBHOOK_URL with job configuration & parameters."""
    webhook_url = getattr(settings, 'N8N_WEBHOOK_URL', 'http://localhost:8088/webhook/startuptn/scrape')
    api_token = (
        getattr(settings, 'N8N_API_TOKEN', '') or getattr(settings, 'N8N_API_KEY', '') or ''
    ).strip()

    payload = {
        "job_id": str(job.id),
        "source": "startuptn",
        "prompt": getattr(job, 'prompt', None) or (
            "Find Tamil Nadu startups and technology companies. Extract company name, founders, "
            "sector, team size, location, website, email, phone number, description, key highlights and StartupTN-related information."
        ),
        "location": getattr(job, 'location', None) or "Tamil Nadu",
        "sector": getattr(job, 'sector', None) or "",
        "max_results": getattr(job, 'company_limit', 0) or 100,
        "requested_by": "system",
    }

    headers = {"Content-Type": "application/json"}
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"
        headers["X-API-Key"] = api_token

    try:
        logger.info(f"[N8N-TRIGGER] Triggering n8n webhook at {webhook_url} for job #{job.id}")
        response = requests.post(webhook_url, json=payload, headers=headers, timeout=15)
        if response.status_code in (200, 201, 202):
            logger.info(f"[N8N-TRIGGER] Successfully triggered n8n webhook for job #{job.id}")
            return True, "n8n webhook triggered successfully"
        else:
            err_msg = f"n8n webhook returned status code {response.status_code}: {response.text[:200]}"
            logger.error(f"[N8N-TRIGGER-ERROR] {err_msg}")
            return False, err_msg
    except requests.exceptions.RequestException as exc:
        err_msg = "Unable to connect to n8n webhook."
        logger.error(f"[N8N-TRIGGER-ERROR] Connection to n8n failed: {exc}")
        return False, err_msg


class N8NClient:
    def __init__(self):
        self.webhook_url = getattr(
            settings,
            'N8N_WEBHOOK_URL',
            'http://localhost:8088/webhook/startuptn/scrape'
        )
        self.webhook_url = self.webhook_url.rstrip('/')
        if 'webhook-start-scraper' in self.webhook_url:
            self.webhook_url = self.webhook_url.replace('webhook-start-scraper', 'startuptn/scrape')
        elif not self.webhook_url.endswith('/webhook/startuptn/scrape'):
            if self.webhook_url.endswith('/webhook'):
                self.webhook_url = self.webhook_url + '/startuptn/scrape'
            elif self.webhook_url.endswith('/webhook/'):
                self.webhook_url = self.webhook_url + 'startuptn/scrape'
            elif 'startuptn/scrape' not in self.webhook_url:
                self.webhook_url = self.webhook_url + '/webhook/startuptn/scrape'
        logger.info("n8n webhook client configured for %s", self._safe_url(self.webhook_url))

    @staticmethod
    def _safe_url(url: str) -> str:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    def trigger_scraper(self, job_id=None, extra_payload=None):
        payload = {
            "source": "django",
            "action": "start_scraper",
            "timestamp": timezone.now().isoformat(),
        }
        if job_id is not None:
            payload["job_id"] = job_id
        if extra_payload:
            payload.update(extra_payload)

        safe_url = self._safe_url(self.webhook_url)
        logger.info("Creating scraper job %s; calling n8n webhook %s", job_id, safe_url)

        try:
            headers = {"Content-Type": "application/json"}
            api_key = (getattr(settings, 'N8N_API_KEY', '') or '').strip()
            if api_key:
                headers["X-API-Key"] = api_key
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            logger.info("n8n response status=%s for %s", response.status_code, safe_url)

            response.raise_for_status()

            try:
                resp_json = response.json()
            except Exception:
                resp_json = response.text

            logger.info("n8n response received for job %s", job_id)
            return {
                "status": "started",
                "message": "n8n workflow triggered successfully",
                "n8n_response": resp_json
            }
        except requests.exceptions.Timeout:
            error_msg = f"n8n request timed out after 10s calling {safe_url}"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
        except requests.exceptions.ConnectionError:
            error_msg = f"Failed to connect to n8n webhook at {safe_url}. Ensure n8n is running."
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
        except requests.exceptions.HTTPError as exc:
            status_code = getattr(exc.response, 'status_code', 'unknown')
            body = getattr(exc.response, 'text', '') if hasattr(exc, 'response') else ''
            error_msg = f"n8n webhook returned HTTP {status_code} for {safe_url}"
            logger.error("%s. Response body: %s", error_msg, body[:500] if body else '<empty>')
            return {"status": "error", "message": error_msg}
        except requests.exceptions.RequestException as exc:
            error_msg = f"n8n webhook error while calling {safe_url}: {exc}"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
