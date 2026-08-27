from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmailCampaignViewSet, CampaignDeliveryListView, CampaignDeliveryDetailView, MarketingStatsView

router = DefaultRouter()
router.register(r'campaigns', EmailCampaignViewSet, basename='campaign')

urlpatterns = [
    path('', include(router.urls)),
    path('deliveries/', CampaignDeliveryListView.as_view(), name='delivery-list'),
    path('deliveries/<int:pk>/', CampaignDeliveryDetailView.as_view(), name='delivery-detail'),
    path('stats/', MarketingStatsView.as_view(), name='marketing-stats'),
]
