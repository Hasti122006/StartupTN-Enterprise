from rest_framework import serializers
from .models import EmailCampaign, CampaignDelivery


class EmailCampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailCampaign
        fields = '__all__'
        read_only_fields = ('id', 'sent_count', 'failed_count', 'created_at', 'updated_at')

    def validate(self, data):
        status = data.get('status')
        scheduled_time = data.get('scheduled_time')
        
        if status == 'scheduled' and not scheduled_time:
            raise serializers.ValidationError("Scheduled campaigns must have a scheduled time.")
            
        return data


class CampaignDeliverySerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.company_name', read_only=True)
    campaign_name = serializers.CharField(source='campaign.name', read_only=True)
    campaign_subject = serializers.CharField(source='campaign.subject', read_only=True)
    campaign_body = serializers.CharField(source='campaign.body', read_only=True)
    founders = serializers.CharField(source='company.founders', read_only=True)

    class Meta:
        model = CampaignDelivery
        fields = '__all__'
        read_only_fields = ('id',)
