import os
import sys
import django

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.test import RequestFactory
from apps.scraper.views import ScraperStartView, ScraperN8nResultsView
from apps.companies.views import CompanyListView, CompanyDetailView
from apps.jobs.views import JobListCreateView
from apps.scraper.models import Job
from apps.companies.models import Company
from django.conf import settings

def run_tests():
    rf = RequestFactory()
    token = getattr(settings, 'N8N_API_TOKEN', '') or getattr(settings, 'N8N_API_KEY', '') or 'startuptn-secret-key-2026'

    # Clear active jobs and test companies for clean test environment
    Job.objects.filter(status__in=['pending', 'running', 'queued']).update(status='stopped')
    Company.objects.filter(profile_url__contains="test-").delete()
    Company.objects.filter(profile_url__contains="ecoclean").delete()

    print("=== TEST 1: Unauthenticated request to n8n Ingestion API ===")
    req1 = rf.post('/scraper/n8n/results/', {}, content_type='application/json')
    resp1 = ScraperN8nResultsView.as_view()(req1)
    print(f"Status Code: {resp1.status_code} (Expected 401)")
    assert resp1.status_code == 401, f"Expected 401, got {resp1.status_code}"

    print("\n=== TEST 2: ScraperStartView when n8n is offline ===")
    req2 = rf.post('/scraper/start', {'company_limit': 5}, content_type='application/json')
    resp2 = ScraperStartView.as_view()(req2)
    print(f"Status Code: {resp2.status_code}")
    print(f"Response Data: {resp2.data}")
    # Should create job and attempt n8n POST; if n8n offline returns 503 with 'Unable to connect to n8n webhook.'
    assert resp2.status_code in (201, 503), f"Unexpected status {resp2.status_code}"
    job_id = resp2.data.get('job_id')
    assert job_id is not None, "job_id should be created"
    job = Job.objects.get(id=job_id)
    print(f"Created Job #{job.id} Status: {job.status}")

    print("\n=== TEST 3: n8n Ingestion API with Valid Data ===")
    payload3 = {
        "job_id": job.id,
        "n8n_execution_id": "exec-test-999",
        "n8n_workflow_id": "wf-test-111",
        "companies": [
            {
                "company_name": "Test Enterprise Tech Pvt Ltd",
                "founders": ["Aravind Kumar", "Suresh Raina"],
                "sector": "Fintech",
                "current_stage": "Series A",
                "team_size": "25-50",
                "location": "Chennai, Tamil Nadu",
                "website": "https://testenterprisetech.com",
                "email": "contact@testenterprisetech.com",
                "phone": "+91 9123456789",
                "smart_card_number": "SC-CHE-2024-001",
                "engagement_level": "High",
                "member_since": "2023",
                "key_highlights": ["Top 10 Fintech Startup", "ISO 27001 Certified"],
                "about": "Pioneering financial automation for Indian enterprises.",
                "source_url": "https://startuptn.in/company/test-enterprise-tech"
            },
            {
                "company_name": "EcoClean Energy Private Limited",
                "founders": ["Meena Sundar"],
                "sector": "CleanTech",
                "current_stage": "Seed",
                "team_size": "5-10",
                "location": "Madurai, Tamil Nadu",
                "website": "https://ecocleanenergy.in",
                "email": "info@ecocleanenergy.in",
                "phone": "+91 9876543210",
                "smart_card_number": "SC-MAD-2024-005",
                "engagement_level": "Medium",
                "member_since": "2024",
                "key_highlights": ["Zero Emission Award 2024"],
                "about": "Solar and clean energy generation technology.",
                "source_url": "https://startuptn.in/company/ecoclean-energy"
            }
        ]
    }
    req3 = rf.post('/scraper/n8n/results/', payload3, content_type='application/json', HTTP_AUTHORIZATION=f'Bearer {token}')
    resp3 = ScraperN8nResultsView.as_view()(req3)
    print(f"Status Code: {resp3.status_code} (Expected 200)")
    print(f"Ingestion Result: {resp3.data}")
    assert resp3.status_code == 200
    assert resp3.data.get('created') == 2
    assert resp3.data.get('updated') == 0

    print("\n=== TEST 4: Duplicate Company Handling (Update Flow) ===")
    # Re-submit company 1 with an updated field
    payload4 = {
        "job_id": job.id,
        "n8n_execution_id": "exec-test-999",
        "n8n_workflow_id": "wf-test-111",
        "companies": [
            {
                "company_name": "Test Enterprise Tech Pvt Ltd",
                "founders": ["Aravind Kumar", "Suresh Raina", "Venkatesh N"],
                "sector": "Fintech & Banking",
                "current_stage": "Series A",
                "team_size": "50-100",
                "location": "Chennai, Tamil Nadu",
                "website": "https://testenterprisetech.com",
                "email": "contact@testenterprisetech.com",
                "phone": "+91 9123456789",
                "smart_card_number": "SC-CHE-2024-001",
                "engagement_level": "Enterprise",
                "member_since": "2023",
                "key_highlights": ["Top 10 Fintech Startup", "ISO 27001 Certified", "Series A Funded"],
                "about": "Pioneering financial automation for Indian enterprises.",
                "source_url": "https://startuptn.in/company/test-enterprise-tech"
            }
        ]
    }
    req4 = rf.post('/scraper/n8n/results/', payload4, content_type='application/json', HTTP_AUTHORIZATION=f'Bearer {token}')
    resp4 = ScraperN8nResultsView.as_view()(req4)
    print(f"Status Code: {resp4.status_code} (Expected 200)")
    print(f"Ingestion Result: {resp4.data}")
    assert resp4.status_code == 200
    assert resp4.data.get('created') == 0
    assert resp4.data.get('updated') == 1

    print("\n=== TEST 5: Verify Ingested Data via Companies API ===")
    c = Company.objects.get(profile_url="https://startuptn.in/company/test-enterprise-tech")
    req5 = rf.get(f'/companies/{c.id}')
    resp5 = CompanyDetailView.as_view()(req5, pk=c.id)
    print(f"Company Detail API Data:")
    for field in ['company_name', 'founders', 'sector', 'team_size', 'smart_card_number', 'engagement_level', 'member_since', 'key_highlights', 'about', 'location', 'website', 'phone']:
        print(f"  {field}: {resp5.data.get(field)}")
        assert resp5.data.get(field) is not None, f"Field {field} should not be None"

    print("\n=== TEST 6: Verify Job Status & Execution Metrics ===")
    job.refresh_from_db()
    print(f"Job #{job.id} Status: {job.status}")
    print(f"Job Scraped Companies: {job.scraped_companies}")
    print(f"Job Created Records: {job.created_records}")
    print(f"Job Updated Records: {job.updated_records}")
    print(f"Job n8n Execution ID: {job.n8n_execution_id}")
    assert job.status == 'completed'
    assert job.updated_records == 1
    assert job.n8n_execution_id == "exec-test-999"

    print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    run_tests()
