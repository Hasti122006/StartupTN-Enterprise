from django.contrib import admin
from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('id', 'company_name', 'sector', 'current_stage', 'location', 'founders', 'scraped_at')
    list_filter = ('sector', 'current_stage', 'scraped_at')
    search_fields = ('company_name', 'founders', 'location', 'sector')
    ordering = ('-scraped_at',)
