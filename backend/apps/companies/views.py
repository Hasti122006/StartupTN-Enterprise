import math
from rest_framework import generics, permissions, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from django.db.models.functions import TruncDate

from .models import Company
from .serializers import CompanySerializer


class CompanyListView(generics.ListAPIView):
    serializer_class = CompanySerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['sector', 'current_stage', 'location', 'job']
    search_fields = ['company_name', 'founders', 'sector', 'location', 'about']
    ordering_fields = ['company_name', 'scraped_at']

    def get_queryset(self):
        return Company.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page_num = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))

        total = queryset.count()
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        start = (page_num - 1) * page_size
        end = start + page_size
        items = queryset[start:end]

        serializer = self.get_serializer(items, many=True)
        return Response({
            'total': total,
            'page': page_num,
            'page_size': page_size,
            'total_pages': total_pages,
            'items': serializer.data,
        })


class CompanyDetailView(generics.RetrieveUpdateAPIView):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'pk'


class SectorStatsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        stats = (
            Company.objects.exclude(sector__isnull=True)
            .exclude(sector='')
            .values('sector')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        return Response(list(stats))


class StageStatsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        stats = (
            Company.objects.exclude(current_stage__isnull=True)
            .exclude(current_stage='')
            .values('current_stage')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        result = [{'stage': item['current_stage'], 'count': item['count']} for item in stats]
        return Response(result)


class DailyStatsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        stats = (
            Company.objects.annotate(date=TruncDate('scraped_at'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('-date')[:7]
        )
        result = [{'date': str(item['date']), 'count': item['count']} for item in stats]
        return Response(result)


class FilterSectorsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        sectors = (
            Company.objects.exclude(sector__isnull=True)
            .exclude(sector='')
            .values_list('sector', flat=True)
            .distinct()
        )
        return Response(list(sectors))


class FilterStagesView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        stages = (
            Company.objects.exclude(current_stage__isnull=True)
            .exclude(current_stage='')
            .values_list('current_stage', flat=True)
            .distinct()
        )
        return Response(list(stages))
