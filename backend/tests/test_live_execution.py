import os
import sys
import time
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.development'
django.setup()

from django.test import RequestFactory
from apps.scraper.views import ScraperStartView
from apps.scraper.models import Job
from apps.companies.models import Company

print("=== EXECUTING REAL STARTUPTN SCRAPER LIVE JOB ===")

# Clear any active job
Job.objects.filter(status__in=['pending', 'running', 'queued']).update(status='stopped')

rf = RequestFactory()
payload = {
    "start_page": 12,
    "end_page": 12,
    "company_limit": 5,
    "workers": 2,
    "test_mode": True
}

req = rf.post('/api/scraper/start', payload, content_type='application/json')
resp = ScraperStartView.as_view()(req)
print(f"Start API Status: {resp.status_code}")
print(f"Response Data: {resp.data}")

job_id = resp.data.get('job_id') or resp.data.get('id')
assert job_id is not None, "Job ID must be returned"

print(f"Monitoring Job #{job_id}...")
for i in range(40):
    time.sleep(2)
    job = Job.objects.get(id=job_id)
    print(f"[{i*2}s] Job #{job.id} status: {job.status} | scraped: {job.scraped_companies} | failed: {job.failed_companies}")
    if job.status in ['completed', 'failed', 'stopped']:
        break

job.refresh_from_db()
print("\n=== FINAL LIVE EXECUTION RESULT ===")
print(f"Job ID: {job.id}")
print(f"Final Status: {job.status}")
print(f"Scraped Companies: {job.scraped_companies}")
print(f"Failed Companies: {job.failed_companies}")
print(f"Created Records: {job.created_records}")
print(f"Updated Records: {job.updated_records}")

companies = Company.objects.filter(job=job)
print(f"\nCompanies in DB for Job #{job.id}: {companies.count()}")
for c in companies[:10]:
    print(f"  - {c.company_name} ({c.sector or 'N/A'}) [{c.location or 'N/A'}] - Profile: {c.profile_url}")
