from django.contrib import admin
from .models import Log


@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ('id', 'job', 'level', 'message', 'page', 'company', 'created_at')
    list_filter = ('level', 'created_at')
    search_fields = ('message', 'company')
    ordering = ('-created_at',)
