import math

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from datetime import date

from .models import Job
from .serializers import JobSerializer
from apps.companies.models import Company


class JobListCreateView(generics.ListCreateAPIView):
    serializer_class = JobSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Job.objects.all()
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page_num = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))

        total = queryset.count()
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return Response({
                'total': total,
                'page': page_num,
                'page_size': page_size,
                'total_pages': total_pages,
                'items': serializer.data,
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'total': total,
            'page': 1,
            'page_size': total,
            'total_pages': 1,
            'items': serializer.data,
        })


class JobDetailDeleteView(generics.RetrieveDestroyAPIView):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'pk'


class JobsSummaryView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        total_companies = Company.objects.count()
        running_jobs = Job.objects.filter(status='running').count()
        failed_jobs = Job.objects.filter(status='failed').count()
        today_jobs = Job.objects.filter(created_at__date=date.today()).count()
        completed_jobs = Job.objects.filter(status='completed').count()

        return Response({
            "total_companies": total_companies,
            "running_jobs": running_jobs,
            "failed_jobs": failed_jobs,
            "today_jobs": today_jobs,
            "completed_jobs": completed_jobs,
        })
