from django.db import models
from apps.scraper.models import Job


class Company(models.Model):
    company_name = models.CharField(max_length=500, db_index=True)
    founders = models.TextField(null=True, blank=True)
    sector = models.TextField(null=True, blank=True)
    current_stage = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    team_size = models.CharField(max_length=100, null=True, blank=True)
    member_since = models.CharField(max_length=100, null=True, blank=True)
    key_highlights = models.TextField(null=True, blank=True)
    about = models.TextField(null=True, blank=True)
    website = models.URLField(max_length=1000, null=True, blank=True)
    linkedin = models.URLField(max_length=1000, null=True, blank=True)
    email = models.CharField(max_length=500, null=True, blank=True)
    phone = models.CharField(max_length=255, null=True, blank=True)
    location = models.CharField(max_length=500, null=True, blank=True, db_index=True)
    engagement_level = models.CharField(max_length=255, null=True, blank=True)
    smart_card_number = models.CharField(max_length=255, null=True, blank=True)
    startup_type = models.CharField(max_length=255, null=True, blank=True)
    ecosystem_category = models.CharField(max_length=255, null=True, blank=True)
    team_members = models.TextField(null=True, blank=True)
    profile_url = models.URLField(max_length=255, unique=True)
    logo_url = models.URLField(max_length=2000, null=True, blank=True)

    job = models.ForeignKey(
        Job,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='companies'
    )
    scraped_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'companies'
        ordering = ['-scraped_at']

    def __str__(self):
        return self.company_name
