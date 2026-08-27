import os
import sys
import django
import asyncio

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from apps.scraper.models import Job
from django.utils import timezone


def create_scraper_job():
    job = Job.objects.create(
        status='running',
        start_page=1,
        end_page=1,         # Scrape 1 page for test
        workers=1,
        delay_min=1.0,
        delay_max=2.0,
        retry_count=3,
        timeout=30,
        headless=False,
        test_mode=True,
        company_limit=5,    # Limit to 5 companies for a quick test run
        prompt="Extract TN startups",
        location="Tamil Nadu",
        start_time=timezone.now(),
        started_at=timezone.now()
    )
    return job


def mark_job_status(job_id, status, error_message=None):
    try:
        job = Job.objects.get(id=job_id)
        job.status = status
        if error_message:
            job.error_message = error_message
        job.completed_at = timezone.now()
        job.end_time = timezone.now()
        job.save()
    except Exception as e:
        print(f"Failed to update job status: {e}")


async def run_scraper_async(job_id):
    # 2. Set environment variables for the scraper configuration
    os.environ["SCRAPER_JOB_ID"] = str(job_id)
    os.environ["SCRAPER_START_PAGE"] = "1"
    os.environ["SCRAPER_END_PAGE"] = "1"
    os.environ["SCRAPER_COMPANY_LIMIT"] = "5"
    os.environ["SCRAPER_HEADLESS"] = "false"
    os.environ["USE_SQLITE"] = "true"
    os.environ["REDIS_HOST"] = "127.0.0.1"
    
    # 3. Add scraper directory to python path at index 0 to avoid path shadowing
    scraper_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scraper"))
    sys.path.insert(0, scraper_dir)
    
    # Force reload of config module from scraper directory
    if "config" in sys.modules:
        del sys.modules["config"]
        
    from scraper import StartupTNScraper
    from config import ScraperConfig
    
    config = ScraperConfig()
    
    print("\n[START] Starting Playwright scraper engine...")
    scraper = StartupTNScraper(config)
    await scraper.run()


def main():
    # 1. Create Job synchronously outside event loop
    job = create_scraper_job()
    print(f"\n[INIT] Created Scraper Job #{job.id} in SQLite database.")
    
    # 2. Run the async event loop for the scraper
    try:
        asyncio.run(run_scraper_async(job.id))
        print("\n[SUCCESS] Scraper run completed successfully!")
        mark_job_status(job.id, 'completed')
    except Exception as e:
        print(f"\n[ERROR] Scraper failed with error: {e}")
        mark_job_status(job.id, 'failed', str(e))


if __name__ == "__main__":
    main()
