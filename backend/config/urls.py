from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from apps.scraper.views import HealthView, ApiKeyDebugView


urlpatterns = [
    path('health', HealthView.as_view(), name='health'),
    path('debug/api-key', ApiKeyDebugView.as_view(), name='debug-api-key'),
    path('admin/', admin.site.urls),

    # Scraper & Ingestion API URLs
    path('scraper/', include('apps.scraper.urls')),
    path('api/scraper/', include('apps.scraper.urls')),
    path('companies/', include('apps.companies.urls')),
    path('api/companies/', include('apps.companies.urls')),
    path('jobs/', include('apps.jobs.urls')),
    path('api/jobs/', include('apps.jobs.urls')),
    path('logs/', include('apps.logs.urls')),
    path('api/logs/', include('apps.logs.urls')),
    path('export/', include('apps.exports.urls')),
    path('api/export/', include('apps.exports.urls')),
    path('marketing/', include('apps.marketing.urls')),
    path('api/marketing/', include('apps.marketing.urls')),


    # Swagger Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
