from django.utils import timezone
from apps.scraper.models import Job
now = timezone.now()
job = Job.objects.create(
    status='queued',
    start_page=1,
    end_page=1,
    workers=1,
    delay_min=1.0,
    delay_max=2.0,
    retry_count=1,
    timeout=30,
    headless=True,
    output_excel=False,
    output_csv=False,
    output_database=True,
    test_mode=True,
    company_limit=1,
    created_by=None,
    start_time=now,
    started_at=now,
)
print('JOB_CREATED', job.id)
