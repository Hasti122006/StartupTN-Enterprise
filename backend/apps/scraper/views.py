import logging
import os
import json
import re
import uuid
import requests
from pathlib import Path
import redis
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.conf import settings
from django.utils import timezone
from django.db import transaction as db_transaction

from .models import Job
from .serializers import JobSerializer
from apps.companies.models import Company
from .services.n8n_client import trigger_n8n_scrape_job
from apps.core.redis import (
    check_redis_connection, set_active_job, set_scraper_control, publish_log, get_redis_client, get_scraper_control, publish_scraper_dispatch
)
from .tasks import dispatch_scraper_job

logger = logging.getLogger(__name__)


class HealthView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({"status": "ok"})


class ApiKeyDebugView(APIView):
    """Safe configuration diagnostic; never expose the key value."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({"api_key_loaded": bool(getattr(settings, "N8N_API_KEY", ""))})


class ScraperHealthView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        redis_info = {
            "host": getattr(settings, 'REDIS_HOST', None) or os.getenv('REDIS_HOST'),
            "port": int(getattr(settings, 'REDIS_PORT', None) or os.getenv('REDIS_PORT', '6379')),
            "password_configured": bool(getattr(settings, 'REDIS_PASSWORD', None) or os.getenv('REDIS_PASSWORD', '')),
        }
        redis_reachable = False
        redis_authenticated = False
        try:
            check_redis_connection()
            redis_reachable = True
            redis_authenticated = True
        except redis.exceptions.AuthenticationError:
            redis_reachable = True
            redis_authenticated = False
        except redis.exceptions.RedisError:
            pass

        return Response(
            {
                "status": "ok",
                "redis": {
                    "host": redis_info["host"],
                    "port": redis_info["port"],
                    "password_configured": redis_info["password_configured"],
                    "reachable": redis_reachable,
                    "authenticated": redis_authenticated,
                },
            }
        )


class ScraperAuthStatusView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        storage_state = getattr(settings, 'STARTUPTN_STORAGE_STATE', os.getenv('STARTUPTN_STORAGE_STATE', '.runtime/startuptn-auth-state.json'))
        state_path = Path(storage_state)
        if not state_path.is_absolute():
            state_path = Path(settings.BASE_DIR) / state_path

        # A Playwright storage-state file may contain only analytics/preferences.
        # Treating its mere existence as an authenticated StartupTN session lets the
        # UI promise access that the scraper cannot actually use.
        has_auth_artifact = False
        state_error = None
        if state_path.exists():
            try:
                state = json.loads(state_path.read_text(encoding="utf-8"))
                storage_items = [
                    item
                    for origin in state.get("origins", [])
                    for item in origin.get("localStorage", [])
                ]
                auth_storage_keys = {"token", "jwttoken", "jwt", "authtoken", "accesstoken", "authorization"}
                has_auth_artifact = any(
                    str(item.get("name", "")).lower() in auth_storage_keys
                    or "token" in str(item.get("name", "")).lower()
                    for item in storage_items
                )
                if not has_auth_artifact:
                    # Cookie names vary by the upstream service.  Ignore known
                    # analytics/accessibility cookies, which are not credentials.
                    ignored_cookie_prefixes = ("_ga", "_gid", "_gat", "uw-")
                    has_auth_artifact = any(
                        name and not name.lower().startswith(ignored_cookie_prefixes)
                        for name in (cookie.get("name") for cookie in state.get("cookies", []))
                    )
            except (OSError, ValueError, TypeError) as exc:
                state_error = f"Unable to read authentication state: {exc}"

        return Response({
            "authenticated": has_auth_artifact,
            "state_present": state_path.exists(),
            "login_url": getattr(settings, 'STARTUPTN_LOGIN_URL', 'https://startuptn.in/login'),
            "detail": state_error or (
                "Authentication state contains no credential artifacts; complete the documented manual login flow."
                if state_path.exists() and not has_auth_artifact else None
            ),
        })



def normalize_company_name(name: str) -> str:
    if not name:
        return ""
    s = name.lower()
    s = re.sub(r"\b(private limited|pvt ltd|pvt\. ltd\.|limited|ltd\.|ltd|llp|inc\.|inc|corp\.|corp)\b", "", s)
    s = re.sub(r"[^\w\s]", "", s)
    return " ".join(s.split())


def format_list_field(val: any) -> str | None:
    if val is None:
        return None
    if isinstance(val, list):
        cleaned = [str(x).strip() for x in val if str(x).strip()]
        return ", ".join(cleaned) if cleaned else None
    if isinstance(val, str):
        s = val.strip()
        if s.startswith('[') and s.endswith(']'):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    cleaned = [str(x).strip() for x in parsed if str(x).strip()]
                    return ", ".join(cleaned) if cleaned else None
            except Exception:
                pass
        return s if s else None
    return str(val).strip() or None


def format_highlights_field(val: any) -> str | None:
    if val is None:
        return None
    if isinstance(val, list):
        cleaned = [str(x).strip() for x in val if str(x).strip()]
        return "\n• ".join(cleaned) if cleaned else None
    if isinstance(val, str):
        s = val.strip()
        if s.startswith('[') and s.endswith(']'):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    cleaned = [str(x).strip() for x in parsed if str(x).strip()]
                    return "\n• ".join(cleaned) if cleaned else None
            except Exception:
                pass
        return s if s else None
    return str(val).strip() or None


class ScraperStartView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        logger.info("[SCRAPER-START] Received start request for n8n pipeline")

        existing_job = Job.objects.filter(status__in=['pending', 'starting', 'running', 'queued', 'paused', 'stopping']).order_by('-created_at').first()
        if existing_job:
            logger.info("[SCRAPER-START] Existing active job found id=%s", existing_job.id)
            return Response(
                {"job_id": existing_job.id, "id": existing_job.id, "status": existing_job.status, "message": "Scraper job already active"},
                status=status.HTTP_200_OK
            )

        data = request.data or {}
        test_mode = bool(data.get('test_mode', False))

        try:
            start_page = int(data.get('start_page', 1) or 1)
        except (TypeError, ValueError):
            return Response({"detail": "Start Page must be an integer."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            end_page = int(data.get('end_page', 0) or 0)
        except (TypeError, ValueError):
            return Response({"detail": "End Page must be an integer."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            company_limit = int(data.get('company_limit', 0) or 0)
        except (TypeError, ValueError):
            return Response({"detail": "Company Limit must be an integer."}, status=status.HTTP_400_BAD_REQUEST)

        if start_page < 1:
            return Response({"detail": "Start Page must be at least 1."}, status=status.HTTP_400_BAD_REQUEST)
        if not (end_page == 0 or end_page >= start_page):
            return Response({"detail": "End Page must be 0 (auto) or greater than/equal to Start Page."}, status=status.HTTP_400_BAD_REQUEST)
        if company_limit < 0:
            return Response({"detail": "Company Limit must be zero or a positive integer."}, status=status.HTTP_400_BAD_REQUEST)

        if test_mode and (not company_limit or company_limit == 0):
            company_limit = 5

        prompt = data.get('prompt') or (
            "Find Tamil Nadu startups and technology companies. Extract company name, founders, "
            "sector, team size, location, website, email, phone number, description, key highlights and StartupTN-related information."
        )
        location = data.get('location') or "Tamil Nadu"
        sector = data.get('sector') or ""

        now = timezone.now()
        job = Job.objects.create(
            status='pending',
            start_page=start_page,
            end_page=end_page,
            workers=int(data.get('workers', 2) or 2),
            delay_min=float(data.get('delay_min', 1.0) or 1.0),
            delay_max=float(data.get('delay_max', 3.0) or 3.0),
            retry_count=int(data.get('retry_count', 3) or 3),
            timeout=int(data.get('timeout', 30) or 30),
            headless=bool(data.get('headless', True)),
            output_excel=bool(data.get('output_excel', True)),
            output_csv=bool(data.get('output_csv', True)),
            output_database=bool(data.get('output_database', True)),
            test_mode=test_mode,
            company_limit=company_limit,
            prompt=prompt,
            location=location,
            sector=sector,
            created_by=None,
            start_time=now,
            started_at=now,
        )

        logger.info("[SCRAPER-START] Created job id=%s for worker & n8n trigger", job.id)
        set_active_job(job.id)
        publish_log(job.id, "INFO", f"Job #{job.id} initialized. Starting Playwright scraper & n8n pipeline...")

        dispatch_payload = {
            "job_id": str(job.id),
            "start_page": job.start_page,
            "end_page": job.end_page,
            "company_limit": job.company_limit,
            "workers": job.workers,
            "delay_min": job.delay_min,
            "delay_max": job.delay_max,
            "retry_count": job.retry_count,
            "timeout": job.timeout,
            "headless": job.headless,
            "test_mode": job.test_mode,
            "prompt": job.prompt,
            "sector": job.sector,
            "location": job.location,
        }
        publish_scraper_dispatch(dispatch_payload)

        job.status = 'running'
        job.save(update_fields=['status', 'updated_at'])

        success, msg = trigger_n8n_scrape_job(job)
        if not success:
            logger.warning("[SCRAPER-START] n8n trigger reported warning/error: %s (Worker is executing via Redis)", msg)

        serializer = JobSerializer(job)
        response_data = serializer.data
        response_data["job_id"] = job.id
        response_data["status"] = "running"
        response_data["message"] = "Scraper job dispatched to worker and n8n pipeline"

        return Response(response_data, status=status.HTTP_201_CREATED)


class ScraperScheduledStartView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        existing_job = Job.objects.filter(status__in=['pending', 'running', 'queued']).order_by('-created_at').first()
        if existing_job:
            return Response(
                {"id": existing_job.id, "status": existing_job.status, "message": "Scraper job already active"},
                status=status.HTTP_200_OK
            )

        data = request.data or {}
        now = timezone.now()
        job = Job.objects.create(
            status='pending',
            start_page=data.get('start_page', 1),
            end_page=data.get('end_page', 0),
            workers=data.get('workers', 2),
            delay_min=data.get('delay_min', 1.0),
            delay_max=data.get('delay_max', 3.0),
            retry_count=data.get('retry_count', 3),
            timeout=data.get('timeout', 30),
            headless=data.get('headless', True),
            output_excel=data.get('output_excel', True),
            output_csv=data.get('output_csv', True),
            output_database=data.get('output_database', True),
            prompt=data.get('prompt') or "Find Tamil Nadu startups and technology companies.",
            location=data.get('location') or "Tamil Nadu",
            sector=data.get('sector') or "",
            company_limit=data.get('company_limit', 100),
            created_by=None,
            start_time=now,
            started_at=now,
        )

        success, msg = trigger_n8n_scrape_job(job)

        if not success:
            job.status = 'failed'
            job.error_message = msg
            job.save(update_fields=['status', 'error_message', 'updated_at'])
            return Response({"id": job.id, "status": "failed", "detail": msg}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        job.status = 'running'
        job.save(update_fields=['status', 'updated_at'])
        return Response({"id": job.id, "job_id": job.id, "status": "running", "message": "Scheduled scraper dispatched to n8n"}, status=status.HTTP_202_ACCEPTED)


class ScraperN8nResultsView(APIView):
    permission_classes = [permissions.AllowAny]

    def _validate_auth(self, request):
        if not getattr(settings, 'N8N_API_AUTH_ENABLED', True):
            return True

        expected_token = (
            getattr(settings, 'N8N_API_TOKEN', '') or getattr(settings, 'N8N_API_KEY', '') or ''
        ).strip()
        if not expected_token:
            return True

        auth_header = request.headers.get('Authorization', '')
        api_key_header = request.headers.get('X-API-Key') or request.headers.get('x-api-key') or ''

        token = ""
        if auth_header.startswith('Bearer '):
            token = auth_header[7:].strip()
        elif api_key_header:
            token = api_key_header.strip()

        return token == expected_token

    def post(self, request):
        if not self._validate_auth(request):
            return Response({"detail": "Invalid or missing API token header"}, status=status.HTTP_401_UNAUTHORIZED)

        data = request.data or {}
        job_id = data.get('job_id')
        if not job_id:
            return Response({"detail": "job_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            job = Job.objects.get(id=job_id)
        except (Job.DoesNotExist, ValueError, TypeError):
            return Response({"detail": f"Job #{job_id} not found"}, status=status.HTTP_404_NOT_FOUND)

        companies_data = data.get('companies')
        if not isinstance(companies_data, list):
            return Response({"detail": "companies must be a list"}, status=status.HTTP_400_BAD_REQUEST)

        n8n_exec_id = data.get('n8n_execution_id')
        n8n_wf_id = data.get('n8n_workflow_id')
        if n8n_exec_id:
            job.n8n_execution_id = str(n8n_exec_id)
        if n8n_wf_id:
            job.n8n_workflow_id = str(n8n_wf_id)

        is_final = bool(data.get('is_final', False))

        created_count = 0
        updated_count = 0
        skipped_count = 0
        failed_count = 0

        with db_transaction.atomic():
            for item in companies_data:
                if not isinstance(item, dict):
                    failed_count += 1
                    continue

                raw_name = str(item.get('company_name') or '').strip()
                if not raw_name:
                    skipped_count += 1
                    continue

                founders = format_list_field(item.get('founders'))
                sector = str(item.get('sector')).strip() if item.get('sector') is not None else None
                current_stage = str(item.get('current_stage')).strip() if item.get('current_stage') is not None else None
                team_size = str(item.get('team_size')).strip() if item.get('team_size') is not None else None
                member_since = str(item.get('member_since')).strip() if item.get('member_since') is not None else None
                smart_card_number = str(item.get('smart_card_number')).strip() if item.get('smart_card_number') is not None else None
                engagement_level = str(item.get('engagement_level')).strip() if item.get('engagement_level') is not None else None
                key_highlights = format_highlights_field(item.get('key_highlights'))
                about = str(item.get('about')).strip() if item.get('about') is not None else None
                website = str(item.get('website')).strip() if item.get('website') is not None else None
                linkedin = str(item.get('linkedin')).strip() if item.get('linkedin') is not None else None
                email = str(item.get('email')).strip() if item.get('email') is not None else None
                phone = str(item.get('phone')).strip() if item.get('phone') is not None else None
                startup_type = str(item.get('startup_type')).strip() if item.get('startup_type') is not None else None
                ecosystem_category = str(item.get('ecosystem_category')).strip() if item.get('ecosystem_category') is not None else None
                logo_url = str(item.get('logo_url')).strip() if item.get('logo_url') is not None else None
                source_url = str(item.get('source_url') or item.get('profile_url') or '').strip() or None

                raw_location = item.get('location')
                city = item.get('city')
                state = item.get('state')
                if raw_location:
                    location = str(raw_location).strip()
                elif city or state:
                    location = f"{city or ''}, {state or ''}".strip(', ').strip()
                else:
                    location = None

                existing_company = None

                # Priority 1: Match by source_url/profile_url
                if source_url:
                    existing_company = Company.objects.filter(profile_url=source_url).first()

                # Priority 2: Match by normalized company_name + website
                if not existing_company and website:
                    norm_name = normalize_company_name(raw_name)
                    if norm_name:
                        for c in Company.objects.filter(website__iexact=website):
                            if normalize_company_name(c.company_name) == norm_name:
                                existing_company = c
                                break

                # Priority 3: Match by normalized company_name + location
                if not existing_company and location:
                    norm_name = normalize_company_name(raw_name)
                    if norm_name:
                        for c in Company.objects.filter(location__iexact=location):
                            if normalize_company_name(c.company_name) == norm_name:
                                existing_company = c
                                break

                if existing_company:
                    if raw_name:
                        existing_company.company_name = raw_name
                    if founders is not None:
                        existing_company.founders = founders
                    if sector is not None:
                        existing_company.sector = sector
                    if current_stage is not None:
                        existing_company.current_stage = current_stage
                    if team_size is not None:
                        existing_company.team_size = team_size
                    if member_since is not None:
                        existing_company.member_since = member_since
                    if smart_card_number is not None:
                        existing_company.smart_card_number = smart_card_number
                    if engagement_level is not None:
                        existing_company.engagement_level = engagement_level
                    if key_highlights is not None:
                        existing_company.key_highlights = key_highlights
                    if about is not None:
                        existing_company.about = about
                    if website is not None:
                        existing_company.website = website
                    if linkedin is not None:
                        existing_company.linkedin = linkedin
                    if email is not None:
                        existing_company.email = email
                    if phone is not None:
                        existing_company.phone = phone
                    if location is not None:
                        existing_company.location = location
                    if startup_type is not None:
                        existing_company.startup_type = startup_type
                    if ecosystem_category is not None:
                        existing_company.ecosystem_category = ecosystem_category
                    if logo_url is not None:
                        existing_company.logo_url = logo_url

                    existing_company.job = job
                    existing_company.save()
                    updated_count += 1
                else:
                    final_profile_url = source_url or f"https://startuptn.in/company/{uuid.uuid4().hex[:12]}"
                    Company.objects.create(
                        company_name=raw_name,
                        founders=founders,
                        sector=sector,
                        current_stage=current_stage,
                        team_size=team_size,
                        member_since=member_since,
                        smart_card_number=smart_card_number,
                        engagement_level=engagement_level,
                        key_highlights=key_highlights,
                        about=about,
                        website=website,
                        linkedin=linkedin,
                        email=email,
                        phone=phone,
                        location=location,
                        startup_type=startup_type,
                        ecosystem_category=ecosystem_category,
                        logo_url=logo_url,
                        profile_url=final_profile_url,
                        job=job,
                    )
                    created_count += 1

            now = timezone.now()
            job.created_records += created_count
            job.updated_records += updated_count
            job.skipped_records += skipped_count
            job.failed_companies += failed_count
            job.scraped_companies = job.created_records + job.updated_records
            if not job.total_companies:
                job.total_companies = job.scraped_companies + job.skipped_records + job.failed_companies

            # Only mark completed if:
            #   1. Explicitly requested as completed status OR
            #   2. is_final is True AND (companies list is non-empty OR sent directly from scraper engine)
            #   3. The job is still in an active/running state (not already terminal)
            TERMINAL_STATES = {'completed', 'failed', 'stopped', 'cancelled'}
            source = data.get('source', '')
            is_explicit_final = is_final and (len(companies_data) > 0 or source == 'startuptn_playwright_scraper')
            if (is_explicit_final or data.get('status') == 'completed') and job.status not in TERMINAL_STATES and not job.stop_requested:
                job.status = 'completed'
                job.completed_at = now
                job.end_time = now
                job.progress = 100.0
                if job.started_at or job.start_time:
                    start_ts = job.started_at or job.start_time
                    job.duration = max(0, int((now - start_ts).total_seconds()))

            job.save()

        try:
            publish_log(
                job.id, "INFO",
                f"n8n batch ingested: created={created_count}, updated={updated_count}, skipped={skipped_count}, failed={failed_count}, total_job_scraped={job.scraped_companies}"
            )
        except Exception:
            pass

        return Response({
            "success": True,
            "job_id": job.id,
            "created": created_count,
            "updated": updated_count,
            "skipped": skipped_count,
            "failed": failed_count,
            "total_created": job.created_records,
            "total_updated": job.updated_records,
            "total_scraped": job.scraped_companies,
            "status": job.status,
        })


class ScraperWorkerStartView(APIView):
    permission_classes = [permissions.AllowAny]

    def _api_key_is_enabled(self):
        return getattr(settings, 'N8N_API_AUTH_ENABLED', False)

    def _validate_api_key(self, request):
        if not self._api_key_is_enabled():
            return True

        provided_key = request.headers.get('X-API-Key') or request.headers.get('x-api-key') or request.headers.get('HTTP_X_API_KEY')
        expected_key = (getattr(settings, 'N8N_API_KEY', '') or '').strip()
        if not expected_key:
            logger.error("N8N_API_AUTH_ENABLED is true but N8N_API_KEY is not configured")
            return False
        if not provided_key:
            logger.warning("Blocked worker start request without X-API-Key header")
            return False
        return provided_key == expected_key

    def _extract_job_id(self, request):
        payload = request.data or {}
        job_id = payload.get('job_id')
        if job_id is None and request.method == 'GET':
            job_id = request.GET.get('job_id')
        if job_id is None:
            return None
        try:
            return int(job_id)
        except (TypeError, ValueError):
            raise ValueError('job_id must be an integer')

    def _handle_worker_start(self, request):
        if not self._validate_api_key(request):
            return Response({"detail": "Invalid or missing X-API-Key header"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            job_id = self._extract_job_id(request)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if job_id is None:
            return Response({"detail": "job_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        logger.info(f"[WORKER START] received job_id={job_id}")

        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            return Response({"detail": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

        logger.info(f"[WORKER START] existing job found id={job.id}")

        if job.status in ['running', 'paused']:
            logger.info(f"[WORKER START] existing job already active id={job.id} status={job.status}")
            return Response(
                {"job_id": job.id, "status": job.status, "message": "Scraper worker already active for this job"},
                status=status.HTTP_200_OK
            )

        if job.status not in ['queued', 'pending']:
            return Response(
                {"job_id": job.id, "status": job.status, "message": "Scraper job is already in a terminal state"},
                status=status.HTTP_200_OK
            )

        job.status = 'running'
        job.save(update_fields=['status', 'updated_at'])

        set_active_job(job.id)
        publish_log(job.id, "INFO", f"Scraper job #{job.id} worker started", page=job.start_page)

        logger.info(f"[WORKER START] dispatching scraper job id={job.id}")
        try:
            publish_scraper_dispatch({
                "job_id": str(job.id),
                "start_page": job.start_page,
                "end_page": job.end_page,
                "company_limit": job.company_limit,
                "workers": job.workers,
                "delay_min": job.delay_min,
                "delay_max": job.delay_max,
                "retry_count": job.retry_count,
                "timeout": job.timeout,
                "headless": job.headless,
                "test_mode": job.test_mode,
                "prompt": job.prompt,
                "sector": job.sector,
                "location": job.location,
            })
            dispatch_scraper_job(job.id)
        except Exception as exc:
            logger.error(f"[WORKER START] worker dispatch failed for job {job.id}: {exc}")
            job.status = 'failed'
            job.error_message = str(exc)
            job.save(update_fields=['status', 'error_message', 'updated_at'])
            return Response(
                {"job_id": job.id, "status": "failed", "message": "Scraper worker dispatch failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        logger.info(f"[WORKER START] scraper dispatched id={job.id}")
        return Response(
            {"job_id": job.id, "status": "running", "message": "Scraper worker dispatched"},
            status=status.HTTP_202_ACCEPTED
        )

    def get(self, request):
        return self._handle_worker_start(request)

    def post(self, request):
        return self._handle_worker_start(request)


class ScraperPauseView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, job_id):
        try:
            job = Job.objects.get(pk=job_id, status__in=['running', 'pending', 'starting', 'queued'])
        except Job.DoesNotExist:
            return Response({"detail": f"No running job found with ID #{job_id}"}, status=status.HTTP_404_NOT_FOUND)

        job.status = 'paused'
        job.pause_requested = True
        job.save(update_fields=['status', 'pause_requested', 'updated_at'])
        set_scraper_control(job_id, "pause")
        publish_log(job.id, "INFO", f"Scraper job #{job.id} paused")
        return Response({
            "job_id": job.id,
            "id": job.id,
            "status": "paused",
            "command": "pause",
            "message": "Pause request processed successfully.",
        })


class ScraperResumeView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, job_id):
        try:
            job = Job.objects.get(pk=job_id, status='paused')
        except Job.DoesNotExist:
            return Response({"detail": f"No paused job found with ID #{job_id}"}, status=status.HTTP_404_NOT_FOUND)

        job.status = 'running'
        job.pause_requested = False
        job.save(update_fields=['status', 'pause_requested', 'updated_at'])
        set_scraper_control(job_id, "resume")
        publish_log(job.id, "INFO", f"Scraper job #{job.id} resumed")
        return Response({
            "job_id": job.id,
            "id": job.id,
            "status": "running",
            "command": "resume",
            "message": "Resume request processed successfully.",
        })


class ScraperStopView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, job_id):
        try:
            job = Job.objects.get(pk=job_id, status__in=['running', 'paused', 'pending', 'starting', 'queued', 'stopping'])
        except Job.DoesNotExist:
            return Response({"detail": f"No active job found with ID #{job_id}"}, status=status.HTTP_404_NOT_FOUND)

        now = timezone.now()
        job.status = 'cancelled'
        job.stop_requested = True
        job.completed_at = now
        job.end_time = now
        job.save(update_fields=['status', 'stop_requested', 'completed_at', 'end_time', 'updated_at'])
        set_scraper_control(job_id, "stop")
        publish_log(job.id, "WARNING", f"Scraper job #{job.id} cancelled/stopped")
        return Response({
            "job_id": job.id,
            "id": job.id,
            "status": "cancelled",
            "command": "stop",
            "message": "Stop request processed successfully.",
        })


class ScraperJobDetailStatusView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, job_id):
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            return Response({"detail": f"Job #{job_id} not found"}, status=status.HTTP_404_NOT_FOUND)

        processed = job.scraped_companies + job.failed_companies + job.skipped_records
        total = job.total_companies or job.company_limit or 100
        progress = job.progress
        if progress == 0 and total > 0 and processed > 0:
            progress = round(min((processed / total) * 100, 100), 2)
        if job.status == 'completed':
            progress = 100.0

        return Response({
            "id": job.id,
            "job_id": job.id,
            "status": job.status,
            "progress": progress,
            "processed": processed,
            "created": job.created_records,
            "updated": job.updated_records,
            "skipped": job.skipped_records,
            "failed": job.failed_companies,
            "scraped": job.scraped_companies,
            "total_companies": total,
            "current_page": job.current_page,
            "total_pages": job.total_pages,
            "current_company": job.current_company,
            "started_at": job.started_at or job.start_time,
            "updated_at": job.updated_at,
            "completed_at": job.completed_at or job.end_time,
            "duration": job.duration,
            "error": job.error_message or job.message,
            "n8n_execution_id": job.n8n_execution_id,
            "n8n_workflow_id": job.n8n_workflow_id,
        })


class ScraperStatusView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        req_job_id = request.GET.get('job_id')
        if req_job_id:
            try:
                active = Job.objects.get(id=req_job_id)
            except Job.DoesNotExist:
                active = None
        else:
            active = Job.objects.filter(status__in=['pending', 'starting', 'queued', 'running', 'paused', 'stopping']).order_by('-created_at').first()
            if not active:
                active = Job.objects.order_by('-created_at').first()

        redis_status = {
            "reachable": False,
            "authenticated": False,
        }
        try:
            check_redis_connection()
            redis_status["reachable"] = True
            redis_status["authenticated"] = True
        except redis.exceptions.AuthenticationError:
            redis_status["reachable"] = True
            redis_status["authenticated"] = False
        except redis.exceptions.RedisError:
            pass

        control_command = None
        if active:
            control_command = get_scraper_control(active.id)

        processed = (active.scraped_companies + active.failed_companies + active.skipped_records) if active else 0
        total = (active.total_companies or active.company_limit or 0) if active else 0
        progress = active.progress if active else 0
        if active and active.status == 'completed':
            progress = 100.0

        now = timezone.now()
        elapsed_seconds = None
        if active:
            start_ts = active.started_at or active.start_time
            if active.status in ('running', 'paused', 'starting', 'pending', 'queued', 'stopping'):
                if start_ts:
                    elapsed_seconds = int((now - start_ts).total_seconds())
            elif active.duration is not None:
                elapsed_seconds = active.duration

        return Response({
            "active_job": JobSerializer(active).data if active else None,
            "is_running": active is not None and active.status in ['running', 'starting', 'pending', 'queued'],
            "is_paused": active is not None and active.status == 'paused',
            "is_stopping": active is not None and active.status == 'stopping',
            "is_stopped": active is not None and active.status in ['stopped', 'cancelled'],
            "is_completed": active is not None and active.status == 'completed',
            "is_failed": active is not None and active.status == 'failed',
            "redis": redis_status,
            "job_id": active.id if active else None,
            "id": active.id if active else None,
            "status": active.status if active else "idle",
            "control_command": control_command,
            "progress": progress,
            "total": total,
            "total_pages": active.total_pages if active else 0,
            "current_page": active.current_page if active else 0,
            "current_company": active.current_company if active else None,
            "processed": processed,
            "created": active.created_records if active else 0,
            "updated": active.updated_records if active else 0,
            "skipped": active.skipped_records if active else 0,
            "successful": active.scraped_companies if active else 0,
            "failed": active.failed_companies if active else 0,
            "started_at": active.started_at if active else None,
            "updated_at": active.updated_at if active else None,
            "completed_at": active.completed_at if active else None,
            "duration": active.duration if active else None,
            "elapsed_seconds": elapsed_seconds,
            "error": active.error_message if active else None,
        })
