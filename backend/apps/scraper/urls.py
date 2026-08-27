from django.urls import path
from .views import (
    ScraperStartView, ScraperScheduledStartView, ScraperWorkerStartView,
    ScraperPauseView, ScraperResumeView, ScraperStopView,
    ScraperStatusView, ScraperJobDetailStatusView, ScraperHealthView, ScraperAuthStatusView,
    ScraperN8nResultsView,
)

urlpatterns = [
    path('start', ScraperStartView.as_view(), name='scraper-start'),
    path('scheduled/start', ScraperScheduledStartView.as_view(), name='scraper-scheduled-start'),
    path('worker/start', ScraperWorkerStartView.as_view(), name='scraper-worker-start'),
    path('n8n/results/', ScraperN8nResultsView.as_view(), name='scraper-n8n-results'),
    path('n8n/results', ScraperN8nResultsView.as_view(), name='scraper-n8n-results-no-slash'),
    path('pause/<int:job_id>', ScraperPauseView.as_view(), name='scraper-pause'),
    path('resume/<int:job_id>', ScraperResumeView.as_view(), name='scraper-resume'),
    path('stop/<int:job_id>', ScraperStopView.as_view(), name='scraper-stop'),
    path('jobs/<int:job_id>/pause/', ScraperPauseView.as_view(), name='scraper-job-pause'),
    path('jobs/<int:job_id>/resume/', ScraperResumeView.as_view(), name='scraper-job-resume'),
    path('jobs/<int:job_id>/stop/', ScraperStopView.as_view(), name='scraper-job-stop'),
    path('jobs/<int:job_id>/status/', ScraperJobDetailStatusView.as_view(), name='scraper-job-status-detail'),
    path('jobs/<int:job_id>/status', ScraperJobDetailStatusView.as_view(), name='scraper-job-status-detail-no-slash'),
    path('jobs/<int:job_id>/', ScraperJobDetailStatusView.as_view(), name='scraper-job-detail'),
    path('jobs/<int:job_id>', ScraperJobDetailStatusView.as_view(), name='scraper-job-detail-no-slash'),
    path('status', ScraperStatusView.as_view(), name='scraper-status'),
    path('health', ScraperHealthView.as_view(), name='scraper-health'),
    path('auth-status', ScraperAuthStatusView.as_view(), name='scraper-auth-status'),
]
