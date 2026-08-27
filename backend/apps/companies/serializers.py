from rest_framework import serializers
from .models import Company


class CompanySerializer(serializers.ModelSerializer):
    source_url = serializers.CharField(source='profile_url', read_only=True)
    scraping_job_id = serializers.IntegerField(source='job_id', read_only=True)

    class Meta:
        model = Company
        fields = '__all__'
        read_only_fields = ('id', 'scraped_at', 'updated_at')
