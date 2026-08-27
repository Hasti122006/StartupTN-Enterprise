from unittest.mock import patch
import redis

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.scraper.models import Job


class ScraperEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch("apps.scraper.views.publish_log")
    @patch("apps.scraper.views.set_active_job")
    @patch("apps.scraper.views.check_redis_connection")
    @patch("apps.scraper.views.N8NClient.trigger_scraper", return_value={"status": "started"})
    def test_start_endpoint_creates_single_job_and_dispatches_scraper_once(
        self,
        mock_n8n,
        mock_redis_check,
        mock_set_active_job,
        mock_publish_log,
    ):
        response = self.client.post(
            "/scraper/start",
            {
                "start_page": 1,
                "end_page": 2,
                "workers": 2,
                "delay_min": 1.0,
                "delay_max": 3.0,
                "retry_count": 1,
                "timeout": 30,
                "headless": True,
                "test_mode": True,
                "company_limit": 5,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Job.objects.count(), 1)
        job = Job.objects.first()
        self.assertEqual(response.json()["job_id"], job.id)
        mock_n8n.assert_called_once_with(job_id=job.id)

    @patch("apps.scraper.views.check_redis_connection", side_effect=redis.exceptions.ConnectionError("down"))
    def test_start_returns_clear_error_when_redis_is_unavailable(self, mock_redis_check):
        response = self.client.post("/scraper/start", {}, format="json")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(Job.objects.count(), 0)

    @patch("apps.scraper.views.dispatch_scraper_job")
    @patch("apps.scraper.views.N8NClient")
    @patch("apps.scraper.views.publish_log")
    def test_worker_endpoint_reuses_existing_job_and_dispatches_task_once(self, mock_publish_log, mock_n8n, mock_dispatch):
        job = Job.objects.create(status="pending")
        self.client.credentials(HTTP_X_API_KEY="startuptn-secret-key-2026")

        response = self.client.post(
            "/scraper/worker/start",
            {"job_id": job.id},
            format="json",
        )

        self.assertEqual(response.status_code, 202)
        job.refresh_from_db()
        self.assertEqual(job.status, "queued")
        mock_dispatch.assert_called_once_with(job.id)
        mock_n8n.assert_not_called()

    @patch("apps.scraper.views.check_redis_connection")
    def test_test_mode_requires_exactly_five_companies(self, mock_redis_check):
        response = self.client.post(
            "/scraper/start",
            {"test_mode": True, "company_limit": 4, "username": "user@example.com", "password": "secret123"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Job.objects.count(), 0)

    @patch("apps.scraper.views.N8NClient.trigger_scraper", return_value={"status": "started"})
    @patch("apps.scraper.views.check_redis_connection")
    def test_start_does_not_accept_browser_credentials(self, mock_redis_check, mock_n8n):
        response = self.client.post(
            "/scraper/start",
            {"test_mode": True, "company_limit": 5, "username": "browser@example.com", "password": "must-not-be-used"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Job.objects.count(), 1)
        mock_n8n.assert_called_once()

    @override_settings(N8N_API_AUTH_ENABLED=True, N8N_API_KEY="test-key")
    @patch("apps.scraper.views.dispatch_scraper_job")
    def test_worker_endpoint_rejects_missing_or_invalid_api_key(self, mock_dispatch):
        missing_response = self.client.post("/scraper/worker/start", {"job_id": 1}, format="json")
        self.assertEqual(missing_response.status_code, 401)

        invalid_response = self.client.post(
            "/scraper/worker/start",
            {"job_id": 1},
            format="json",
            HTTP_X_API_KEY="wrong-key",
        )
        self.assertEqual(invalid_response.status_code, 401)
        mock_dispatch.assert_not_called()

    @patch("apps.scraper.views.check_redis_connection")
    def test_scraper_health_reports_redis_state(self, mock_redis):
        response = self.client.get("/scraper/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertTrue(response.json()["redis"]["reachable"])

    @patch("apps.scraper.views.publish_log")
    @patch("apps.scraper.views.dispatch_scraper_job")
    def test_scheduled_endpoint_creates_job_and_dispatches_task(self, mock_dispatch, mock_publish_log):
        response = self.client.post(
            "/scraper/scheduled/start",
            {"start_page": 1, "end_page": 2},
            format="json",
        )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(Job.objects.count(), 1)
        self.assertEqual(response.json()["status"], "queued")
        mock_dispatch.assert_called_once()
