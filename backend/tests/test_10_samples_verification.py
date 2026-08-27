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

def run_10_sample_verification():
    rf = RequestFactory()
    token = getattr(settings, 'N8N_API_TOKEN', '') or getattr(settings, 'N8N_API_KEY', '') or 'startuptn-secret-key-2026'

    print("============================================================")
    print("STARTING FINAL 10-SAMPLE SCRAPER & PIPELINE VERIFICATION RUN")
    print("============================================================")

    # Clean previous test sample companies (keep original non-test DB records intact)
    Company.objects.filter(profile_url__contains="sample-10-").delete()
    Job.objects.filter(prompt__contains="10 StartupTN").update(status='stopped')

    # STEP 1: Create Scraper Job via Django Scraper API
    start_payload = {
        "prompt": "Find 10 StartupTN/Tamil Nadu startup company records and extract all available verified company information. Do not invent missing information. Return all requested fields using the required JSON schema.",
        "location": "Tamil Nadu",
        "sector": "",
        "company_limit": 10,
        "test_mode": False
    }

    req1 = rf.post('/scraper/start', start_payload, content_type='application/json')
    resp1 = ScraperStartView.as_view()(req1)
    print(f"\n[STEP 1] Django Job Trigger API Status: {resp1.status_code}")
    print(f"Response Data: {resp1.data}")

    job_id = resp1.data.get('job_id')
    assert job_id is not None, "Job ID must be returned by Scraper API"
    job = Job.objects.get(id=job_id)
    print(f"Job #{job.id} created with Status: {job.status}")

    # STEP 2: Simulate n8n executing AI scraper and returning 10 structured company records to Django Ingestion API
    sample_companies = [
        {
            "company_name": "Solvetastic Tech Private Limited",
            "founders": ["Karthik V", "Lakshmi Narayanan"],
            "sector": "SaaS & AI",
            "current_stage": "Growth Stage",
            "team_size": "20-50",
            "location": "Chennai, Tamil Nadu",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "website": "https://solvetastic.io",
            "email": "hello@solvetastic.io",
            "phone": "+91 44 45678901",
            "smart_card_number": "STN-CHE-2023-1001",
            "engagement_level": "Platinum",
            "member_since": "2022",
            "key_highlights": ["TANSEED Seed Fund", "100+ Enterprise Clients"],
            "about": "AI-driven customer service automation platform built for global SaaS businesses.",
            "source_url": "https://startuptn.in/company/sample-10-01"
        },
        {
            "company_name": "AgroSprout Technologies Private Limited",
            "founders": ["Ramanathan M", "Anitha M"],
            "sector": "AgriTech",
            "current_stage": "Seed Stage",
            "team_size": "10-20",
            "location": "Coimbatore, Tamil Nadu",
            "city": "Coimbatore",
            "state": "Tamil Nadu",
            "website": "https://agrosprout.in",
            "email": "contact@agrosprout.in",
            "phone": "+91 9442199887",
            "smart_card_number": "STN-COI-2023-1002",
            "engagement_level": "Gold",
            "member_since": "2023",
            "key_highlights": ["Precision Agriculture Patent", "TNAU Incubated"],
            "about": "IoT soil quality sensors and drone spraying for sustainable farming.",
            "source_url": "https://startuptn.in/company/sample-10-02"
        },
        {
            "company_name": "PulseHealth Diagnostics Private Limited",
            "founders": ["Dr. Balaji S", "Dr. Chitra Balaji"],
            "sector": "HealthTech",
            "current_stage": "Series A",
            "team_size": "50-100",
            "location": "Madurai, Tamil Nadu",
            "city": "Madurai",
            "state": "Tamil Nadu",
            "website": "https://pulsehealth.med",
            "email": "care@pulsehealth.med",
            "phone": "+91 452 2345678",
            "smart_card_number": "STN-MAD-2022-1003",
            "engagement_level": "Active",
            "member_since": "2022",
            "key_highlights": ["NABL Accredited", "AI Point-of-Care Diagnostic Device"],
            "about": "Rapid portable blood analyzer for rural health centers.",
            "source_url": "https://startuptn.in/company/sample-10-03"
        },
        {
            "company_name": "CleanWatt Mobility Private Limited",
            "founders": ["Deepak Raj", "Gokul Nath"],
            "sector": "CleanTech & EV",
            "current_stage": "Early Stage",
            "team_size": "15-30",
            "location": "Hosur, Tamil Nadu",
            "city": "Hosur",
            "state": "Tamil Nadu",
            "website": "https://cleanwatt.ev",
            "email": "info@cleanwatt.ev",
            "phone": "+91 4344 987654",
            "smart_card_number": "STN-HOS-2024-1004",
            "engagement_level": "Gold",
            "member_since": "2024",
            "key_highlights": ["Battery Swapping Station Network", "IIT Madras Incubation"],
            "about": "Modular EV battery packs and charging infrastructure for two-wheelers.",
            "source_url": "https://startuptn.in/company/sample-10-04"
        },
        {
            "company_name": "EduSpark Learning Systems Private Limited",
            "founders": ["Eshwar Prasad", "Farida Begum"],
            "sector": "EdTech",
            "current_stage": "Pre-Series A",
            "team_size": "30-50",
            "location": "Tiruchirappalli, Tamil Nadu",
            "city": "Tiruchirappalli",
            "state": "Tamil Nadu",
            "website": "https://eduspark.edu.in",
            "email": "support@eduspark.edu.in",
            "phone": "+91 431 8765432",
            "smart_card_number": "STN-TRY-2023-1005",
            "engagement_level": "Active",
            "member_since": "2023",
            "key_highlights": ["Tamil Language STEM Curriculum", "500+ School Partners"],
            "about": "Gamified vernacular learning platform for K-12 STEM subjects.",
            "source_url": "https://startuptn.in/company/sample-10-05"
        },
        {
            "company_name": "FinFlex Systems Private Limited",
            "founders": ["Ganesh Murthy"],
            "sector": "Fintech",
            "current_stage": "Seed Stage",
            "team_size": "8-15",
            "location": "Salem, Tamil Nadu",
            "city": "Salem",
            "state": "Tamil Nadu",
            "website": "https://finflex.co.in",
            "email": "contact@finflex.co.in",
            "phone": "+91 427 3456789",
            "smart_card_number": "STN-SAL-2024-1006",
            "engagement_level": "Active",
            "member_since": "2024",
            "key_highlights": ["Automated MSME Invoice Discounting"],
            "about": "Fintech platform enabling immediate liquidity for textile MSMEs.",
            "source_url": "https://startuptn.in/company/sample-10-06"
        },
        {
            "company_name": "RoboFab Robotics Private Limited",
            "founders": ["Hariharan K", "Indumathi R"],
            "sector": "DeepTech & Robotics",
            "current_stage": "Growth Stage",
            "team_size": "40-80",
            "location": "Chennai, Tamil Nadu",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "website": "https://robofab.ai",
            "email": "sales@robofab.ai",
            "phone": "+91 44 67890123",
            "smart_card_number": "STN-CHE-2022-1007",
            "engagement_level": "Platinum",
            "member_since": "2022",
            "key_highlights": ["Automotive Assembly Autonomous Robots", "Exported to 5 Countries"],
            "about": "Industrial cobots and computer vision quality inspection systems.",
            "source_url": "https://startuptn.in/company/sample-10-07"
        },
        {
            "company_name": "Oceanic AquaTech Private Limited",
            "founders": ["Jayakumar S"],
            "sector": "Blue Economy & AquaTech",
            "current_stage": "Early Stage",
            "team_size": "10-25",
            "location": "Thoothukudi, Tamil Nadu",
            "city": "Thoothukudi",
            "state": "Tamil Nadu",
            "website": "https://oceanicaqua.in",
            "email": "info@oceanicaqua.in",
            "phone": "+91 461 4567890",
            "smart_card_number": "STN-TUT-2023-1008",
            "engagement_level": "Active",
            "member_since": "2023",
            "key_highlights": ["Blue Economy Startup Award", "Biofloc Water Monitoring"],
            "about": "Automated water quality monitoring for commercial shrimp aquaculture.",
            "source_url": "https://startuptn.in/company/sample-10-08"
        },
        {
            "company_name": "CyberShield Defense Private Limited",
            "founders": ["Krishnan A", "Lavanya K"],
            "sector": "Cybersecurity",
            "current_stage": "Series A",
            "team_size": "30-60",
            "location": "Coimbatore, Tamil Nadu",
            "city": "Coimbatore",
            "state": "Tamil Nadu",
            "website": "https://cybershield.sec",
            "email": "security@cybershield.sec",
            "phone": "+91 422 7890123",
            "smart_card_number": "STN-COI-2022-1009",
            "engagement_level": "Gold",
            "member_since": "2022",
            "key_highlights": ["Zero Trust Cloud Security Patent", "SOC2 Type II Certified"],
            "about": "Continuous automated penetration testing and threat intelligence.",
            "source_url": "https://startuptn.in/company/sample-10-09"
        },
        {
            "company_name": "Biopack Sustainable Materials Private Limited",
            "founders": ["Manikandan P", "Nitya P"],
            "sector": "BioTech & Packaging",
            "current_stage": "Seed Stage",
            "team_size": "12-25",
            "location": "Vellore, Tamil Nadu",
            "city": "Vellore",
            "state": "Tamil Nadu",
            "website": "https://biopack.green",
            "email": "contact@biopack.green",
            "phone": "+91 416 5678901",
            "smart_card_number": "STN-VEL-2023-1010",
            "engagement_level": "Active",
            "member_since": "2023",
            "key_highlights": ["100% Compostable Agricultural Waste Packaging"],
            "about": "Biodegradable packaging alternatives manufactured from sugarcane bagasse.",
            "source_url": "https://startuptn.in/company/sample-10-10"
        }
    ]

    ingestion_payload = {
        "job_id": job.id,
        "n8n_execution_id": "exec-10-samples-verify",
        "n8n_workflow_id": "LiID8F9ndug1s0vH",
        "companies": sample_companies
    }

    req2 = rf.post(
        '/scraper/n8n/results/',
        ingestion_payload,
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {token}'
    )
    resp2 = ScraperN8nResultsView.as_view()(req2)

    print(f"\n[STEP 2] n8n Ingestion API Status: {resp2.status_code}")
    print(f"Ingestion Response Data: {resp2.data}")
    assert resp2.status_code == 200, "Ingestion must return 200 OK"
    assert resp2.data.get('created') == 10, "10 records should be created"

    # STEP 3: Verify Job Record Metrics & Status in DB
    job.refresh_from_db()
    print(f"\n[STEP 3] Job #{job.id} Final Status: {job.status}")
    print(f"  Total Companies Processed: {job.total_companies}")
    print(f"  Created Records: {job.created_records}")
    print(f"  Updated Records: {job.updated_records}")
    print(f"  Skipped Records: {job.skipped_records}")
    print(f"  Failed Companies: {job.failed_companies}")
    print(f"  n8n Execution ID: {job.n8n_execution_id}")

    assert job.status == 'completed', "Job status must be completed"
    assert job.created_records == 10, "Created records must equal 10"

    # STEP 4: Verify List API (`GET /api/companies/`)
    req4 = rf.get('/companies/?page=1&page_size=15')
    resp4 = CompanyListView.as_view()(req4)
    print(f"\n[STEP 4] Company List API Status: {resp4.status_code}")
    print(f"Total Companies in DB: {resp4.data.get('total')}")
    assert resp4.status_code == 200

    # STEP 5: Verify Detail API (`GET /api/companies/<id>/`) for ALL 10 Sample Companies
    print("\n[STEP 5] Verifying Detail API (GET /api/companies/<id>/) for all 10 sample companies:")
    scraped_test_companies = Company.objects.filter(profile_url__contains="sample-10-").order_by('id')
    assert scraped_test_companies.count() == 10, "Exactly 10 test records must exist in database"

    for idx, comp in enumerate(scraped_test_companies, 1):
        req_det = rf.get(f'/companies/{comp.id}/')
        resp_det = CompanyDetailView.as_view()(req_det, pk=comp.id)
        assert resp_det.status_code == 200, f"Detail API for company #{comp.id} failed"
        cdata = resp_det.data

        print(f"\n  Sample #{idx} (ID: {comp.id}) - {cdata.get('company_name')}:")
        print(f"    Founders: {cdata.get('founders')}")
        print(f"    Sector: {cdata.get('sector')}")
        print(f"    Team Size: {cdata.get('team_size')}")
        print(f"    Smart Card #: {cdata.get('smart_card_number')}")
        print(f"    Engagement Level: {cdata.get('engagement_level')}")
        print(f"    Member Since: {cdata.get('member_since')}")
        print(f"    Location: {cdata.get('location')}")
        print(f"    Website: {cdata.get('website')}")

        # Assert every requested field exists and is non-null
        assert cdata.get('company_name') is not None, "company_name missing"
        assert cdata.get('founders') is not None, "founders missing"
        assert cdata.get('sector') is not None, "sector missing"
        assert cdata.get('team_size') is not None, "team_size missing"
        assert cdata.get('smart_card_number') is not None, "smart_card_number missing"
        assert cdata.get('engagement_level') is not None, "engagement_level missing"
        assert cdata.get('member_since') is not None, "member_since missing"
        assert cdata.get('location') is not None, "location missing"
        assert cdata.get('website') is not None, "website missing"

    print("\n============================================================")
    print("SCRAPING & INGESTION STATS SUMMARY:")
    print("  Records Requested: 10")
    print(f"  Records Returned:  10")
    print(f"  Records Inserted:  {job.created_records}")
    print(f"  Records Updated:   {job.updated_records}")
    print(f"  Records Skipped:   {job.skipped_records}")
    print(f"  Records Failed:    {job.failed_companies}")
    print("============================================================")
    print("ALL 10 SAMPLE VERIFICATION CHECKS PASSED PERFECTLY!")

if __name__ == '__main__':
    run_10_sample_verification()
