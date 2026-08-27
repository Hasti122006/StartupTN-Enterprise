from rest_framework import viewsets, permissions, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum
from django.utils import timezone
from .models import EmailCampaign, CampaignDelivery
from .serializers import EmailCampaignSerializer, CampaignDeliverySerializer
from .tasks import trigger_campaign_send


class EmailCampaignViewSet(viewsets.ModelViewSet):
    queryset = EmailCampaign.objects.all()
    serializer_class = EmailCampaignSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        campaign = self.get_object()
        if campaign.status == 'sending':
            return Response(
                {"detail": "Campaign is already sending."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Trigger sending asynchronously (Celery with thread fallback)
        trigger_campaign_send(campaign.id)
        
        return Response({
            "status": "success",
            "message": "Campaign execution started."
        })

    @action(detail=True, methods=['post'])
    def schedule(self, request, pk=None):
        campaign = self.get_object()
        scheduled_time_str = request.data.get('scheduled_time')
        if not scheduled_time_str:
            return Response(
                {"detail": "scheduled_time is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Parse ISO datetime
            scheduled_time = timezone.datetime.fromisoformat(scheduled_time_str.replace('Z', '+00:00'))
        except ValueError:
            return Response(
                {"detail": "Invalid datetime format. Use ISO 8601."},
                status=status.HTTP_400_BAD_REQUEST
            )

        campaign.scheduled_time = scheduled_time
        campaign.status = 'scheduled'
        campaign.save()

        # If the scheduled time is in the past, run it immediately
        if scheduled_time <= timezone.now():
            trigger_campaign_send(campaign.id)
            return Response({
                "status": "success",
                "message": "Scheduled time is in the past. Campaign triggered immediately."
            })

        return Response({
            "status": "success",
            "message": f"Campaign scheduled successfully for {scheduled_time_str}."
        })


class CampaignDeliveryListView(generics.ListCreateAPIView):
    queryset = CampaignDelivery.objects.all()
    serializer_class = CampaignDeliverySerializer
    permission_classes = [permissions.AllowAny]
    ordering_fields = ['sent_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        campaign_id = self.request.query_params.get('campaign')
        if campaign_id:
            queryset = queryset.filter(campaign_id=campaign_id)
        return queryset


class CampaignDeliveryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CampaignDelivery.objects.all()
    serializer_class = CampaignDeliverySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'pk'


class MarketingStatsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        total_campaigns = EmailCampaign.objects.count()
        scheduled_count = EmailCampaign.objects.filter(status='scheduled').count()
        
        stats = EmailCampaign.objects.aggregate(
            sent_sum=Sum('sent_count'),
            failed_sum=Sum('failed_count')
        )
        
        sent_sum = stats.get('sent_sum') or 0
        failed_sum = stats.get('failed_sum') or 0
        total_emails = sent_sum + failed_sum
        
        success_rate = 100.0
        if total_emails > 0:
            success_rate = round((sent_sum / total_emails) * 100, 1)

        return Response({
            "total_campaigns": total_campaigns,
            "scheduled_campaigns": scheduled_count,
            "sent_emails": sent_sum,
            "failed_emails": failed_sum,
            "success_rate": success_rate
        })
