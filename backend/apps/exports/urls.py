from django.urls import path
from .views import ExportExcelView, ExportCsvView, ExportHistoryView, ExportDownloadView

urlpatterns = [
    path('excel', ExportExcelView.as_view(), name='export-excel'),
    path('csv', ExportCsvView.as_view(), name='export-csv'),
    path('download', ExportDownloadView.as_view(), name='export-download'),
    path('history', ExportHistoryView.as_view(), name='export-history'),
]
