import math
from rest_framework import generics, permissions
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Log
from .serializers import LogSerializer


class LogListView(generics.ListAPIView):
    serializer_class = LogSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['job', 'level']

    def get_queryset(self):
        return Log.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page_num = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 100))

        total = queryset.count()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return Response({
                'total': total,
                'page': page_num,
                'page_size': page_size,
                'items': serializer.data,
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'total': total,
            'page': 1,
            'page_size': total,
            'items': serializer.data,
        })
