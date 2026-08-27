from django.urls import path
from .views import JobListCreateView, JobDetailDeleteView, JobsSummaryView

urlpatterns = [
    path('', JobListCreateView.as_view(), name='jobs-list'),
    path('stats/summary', JobsSummaryView.as_view(), name='jobs-summary'),
    path('<int:pk>', JobDetailDeleteView.as_view(), name='jobs-detail-delete'),
]
