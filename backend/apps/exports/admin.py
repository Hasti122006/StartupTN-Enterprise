from django.contrib import admin
from .models import Export


@admin.register(Export)
class ExportAdmin(admin.ModelAdmin):
    list_display = ('id', 'filename', 'file_type', 'total_records', 'file_size', 'created_by', 'created_at')
    list_filter = ('file_type', 'created_at')
    search_fields = ('filename',)
    ordering = ('-created_at',)
