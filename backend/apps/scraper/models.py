from django.db import models
from django.conf import settings


class Job(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('queued', 'Queued'),
        ('running', 'Running'),
        ('paused', 'Paused'),
        ('stopping', 'Stopping'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('stopped', 'Stopped'),
        ('cancelled', 'Cancelled'),
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    progress = models.FloatField(default=0.0)
    stop_requested = models.BooleanField(default=False)
    pause_requested = models.BooleanField(default=False)
    current_page = models.PositiveIntegerField(default=0)
    current_company = models.CharField(max_length=500, null=True, blank=True)
    total_pages = models.PositiveIntegerField(default=0)
    total_companies = models.PositiveIntegerField(default=0)
    scraped_companies = models.PositiveIntegerField(default=0)
    failed_companies = models.PositiveIntegerField(default=0)

    start_page = models.PositiveIntegerField(default=1)
    end_page = models.PositiveIntegerField(default=0)
    workers = models.PositiveSmallIntegerField(default=2)
    delay_min = models.FloatField(default=1.0)
    delay_max = models.FloatField(default=3.0)
    retry_count = models.PositiveSmallIntegerField(default=3)
    timeout = models.PositiveIntegerField(default=30)
    headless = models.BooleanField(default=True)
    output_excel = models.BooleanField(default=True)
    output_csv = models.BooleanField(default=True)
    output_database = models.BooleanField(default=True)
    test_mode = models.BooleanField(default=False)
    company_limit = models.PositiveSmallIntegerField(default=0, help_text="0 means no profile limit")

    message = models.TextField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    prompt = models.TextField(null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    sector = models.CharField(max_length=255, null=True, blank=True)

    n8n_execution_id = models.CharField(max_length=255, null=True, blank=True)
    n8n_workflow_id = models.CharField(max_length=255, null=True, blank=True)
    created_records = models.PositiveIntegerField(default=0)
    updated_records = models.PositiveIntegerField(default=0)
    skipped_records = models.PositiveIntegerField(default=0)
    start_time = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration = models.PositiveIntegerField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='jobs'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'jobs'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.start_time and not self.started_at:
            self.started_at = self.start_time
        elif self.started_at and not self.start_time:
            self.start_time = self.started_at
        if self.end_time and not self.completed_at:
            self.completed_at = self.end_time
        elif self.completed_at and not self.end_time:
            self.end_time = self.completed_at
        if self.error_message and not self.message:
            self.message = self.error_message
        elif self.message and not self.error_message:
            self.error_message = self.message
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Job #{self.id} [{self.status}]"
