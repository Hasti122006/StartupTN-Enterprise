from django.contrib import admin
from .models import Job

if not admin.site.is_registered(Job):
    @admin.register(Job)
    class JobAdmin(admin.ModelAdmin):
        list_display = (
            'id', 'status', 'current_page', 'total_pages',
            'scraped_companies', 'failed_companies', 'workers', 'start_time', 'duration'
        )
        list_filter = ('status', 'headless', 'created_at')
        search_fields = ('current_company', 'error_message')
        ordering = ('-created_at',)
