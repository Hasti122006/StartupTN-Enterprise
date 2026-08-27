from rest_framework import serializers
from .models import Export


class ExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Export
        fields = '__all__'
        read_only_fields = ('id', 'created_at')
