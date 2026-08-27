import os
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import FileResponse
from django.shortcuts import get_object_or_404

from .models import Export
from .serializers import ExportSerializer
from .services import ExportService
from apps.companies.models import Company
from django.db.models import Q


class ExportExcelView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        job_id = request.query_params.get('job_id')
        try:
            file_path = ExportService.generate_excel(job_id=job_id, user=None)
            response = FileResponse(
                open(file_path, 'rb'),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
            return response
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_404_NOT_FOUND)


class ExportCsvView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        job_id = request.query_params.get('job_id')
        try:
            file_path = ExportService.generate_csv(job_id=job_id, user=None)
            response = FileResponse(
                open(file_path, 'rb'),
                content_type='text/csv'
            )
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
            return response
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_404_NOT_FOUND)


class ExportDownloadView(APIView):
    """Download export for scope: all | selected | filtered. POST accepts JSON payload.

    Examples:
    { "scope": "all", "format": "xlsx" }
    { "scope": "selected", "ids": [1,2,3], "format": "csv" }
    { "scope": "filtered", "filters": {"search": "ai", "sector": "Fintech"}, "format": "xlsx" }
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        payload = request.data or {}
        scope = str(payload.get('scope', 'all')).lower()
        fmt = str(payload.get('format', 'xlsx')).lower()
        job_id = payload.get('job_id')

        try:
            if scope == 'all':
                qs = Company.objects.all().order_by('-scraped_at')
            elif scope == 'selected':
                ids = payload.get('ids') or []
                if not ids:
                    return Response({'detail': 'Select at least one company.'}, status=status.HTTP_400_BAD_REQUEST)
                qs = Company.objects.filter(id__in=ids).order_by('-scraped_at')
            elif scope == 'filtered':
                filters = payload.get('filters', {}) or {}
                qs = Company.objects.all()
                search = filters.get('search')
                if search:
                    qs = qs.filter(
                        Q(company_name__icontains=search) | Q(founders__icontains=search) | Q(about__icontains=search)
                    )
                sector = filters.get('sector')
                if sector:
                    qs = qs.filter(sector=sector)
                stage = filters.get('current_stage') or filters.get('stage')
                if stage:
                    qs = qs.filter(current_stage=stage)
                location = filters.get('location')
                if location:
                    qs = qs.filter(location=location)
                qs = qs.order_by('-scraped_at')
            else:
                return Response({'detail': 'Invalid scope'}, status=status.HTTP_400_BAD_REQUEST)

            if not qs.exists():
                return Response({'detail': 'No companies available for export.'}, status=status.HTTP_404_NOT_FOUND)

            if fmt in ('xlsx', 'xls', 'excel'):
                file_path = ExportService.generate_excel(job_id=job_id, user=None, queryset=qs)
                content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            else:
                file_path = ExportService.generate_csv(job_id=job_id, user=None, queryset=qs)
                content_type = 'text/csv'

            response = FileResponse(open(file_path, 'rb'), content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
            return response
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ExportHistoryView(generics.ListAPIView):
    queryset = Export.objects.all().order_by('-created_at')
    serializer_class = ExportSerializer
    permission_classes = [permissions.AllowAny]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

