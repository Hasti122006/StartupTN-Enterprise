from django.urls import path
from .views import (
    CompanyListView, CompanyDetailView, SectorStatsView,
    StageStatsView, DailyStatsView, FilterSectorsView, FilterStagesView,
)

urlpatterns = [
    path('', CompanyListView.as_view(), name='companies-list'),
    path('stats/sectors', SectorStatsView.as_view(), name='companies-stats-sectors'),
    path('stats/stages', StageStatsView.as_view(), name='companies-stats-stages'),
    path('stats/daily', DailyStatsView.as_view(), name='companies-stats-daily'),
    path('filters/sectors', FilterSectorsView.as_view(), name='companies-filters-sectors'),
    path('filters/stages', FilterStagesView.as_view(), name='companies-filters-stages'),
    path('<int:pk>', CompanyDetailView.as_view(), name='companies-detail'),
    path('<int:pk>/', CompanyDetailView.as_view(), name='companies-detail-slash'),
]
