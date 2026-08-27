from django.contrib import admin
from .models import Job

if not admin.site.is_registered(Job):
    @admin.register(Job)
    class JobAdmin(admin.ModelAdmin):
        list_display = ('id', 'status', 'progress', 'current_page', 'scraped_companies', 'failed_companies', 'created_at')
        list_filter = ('status', 'created_at')
        search_fields = ('current_company', 'error_message', 'message')
