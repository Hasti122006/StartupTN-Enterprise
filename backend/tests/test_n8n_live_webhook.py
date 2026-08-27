import os
import sys
import time
import requests

import django
BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.scraper.models import Job
from apps.companies.models import Company

def test_live_n8n_webhook():
    print("============================================================")
    print("TESTING LIVE N8N WEBHOOK -> DJANGO INGESTION PIPELINE")
    print("============================================================")

    job = Job.objects.create(
        status='pending',
        prompt='Live n8n test 2 companies',
        company_limit=2,
        test_mode=True
    )
    print(f"Created Job #{job.id} in Django DB.")

    webhook_url = os.getenv('N8N_WEBHOOK_URL', 'http://localhost:8088/webhook/startuptn/scrape')
    payload = {
        "job_id": str(job.id),
        "prompt": "Find Tamil Nadu startups and technology companies.",
        "location": "Tamil Nadu",
        "sector": "AgriTech",
        "max_results": 2,
        "source": "startuptn"
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer startuptn-secret-key-2026",
        "X-API-Key": "startuptn-secret-key-2026"
    }

    print(f"Triggering n8n webhook at: {webhook_url}")
    try:
        res = requests.post(webhook_url, json=payload, headers=headers, timeout=15)
        print(f"n8n Webhook HTTP Status: {res.status_code}")
        print(f"n8n Response Text: {res.text}")
        assert res.status_code == 200, f"Expected 200 OK from n8n webhook, got {res.status_code}"
    except Exception as exc:
        print(f"n8n Trigger Failed: {exc}")
        raise

    print("Waiting 5s for n8n background execution -> Django HTTP POST ingestion API...")
    time.sleep(5)

    job.refresh_from_db()
    print(f"Job #{job.id} Final Status: {job.status}")
    print(f"  scraped_companies: {job.scraped_companies}")
    print(f"  created_records: {job.created_records}")
    print(f"  updated_records: {job.updated_records}")

    companies = Company.objects.filter(job=job)
    print(f"Companies linked to Job #{job.id}: {companies.count()}")
    for c in companies:
        print(f"  - {c.company_name} ({c.sector}) [{c.location}]")

    assert job.status == 'completed', f"Job status should be 'completed', got {job.status}"
    assert companies.count() > 0, "Companies should be saved in DB from n8n pipeline"
    print("SUCCESS: Live n8n webhook -> Django Ingestion -> DB flow verified cleanly!")

if __name__ == "__main__":
    test_live_n8n_webhook()

