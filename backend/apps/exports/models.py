from django.db import models
from django.conf import settings
from apps.jobs.models import Job


class Export(models.Model):
    TYPE_CHOICES = (
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    )

    filename = models.CharField(max_length=500)
    file_type = models.CharField(max_length=20, choices=TYPE_CHOICES, db_index=True)
    file_path = models.CharField(max_length=1000)
    file_size = models.BigIntegerField(null=True, blank=True)
    total_records = models.PositiveIntegerField(null=True, blank=True)

    job = models.ForeignKey(
        Job,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='exports'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='exports'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'exports'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.filename} ({self.file_type})"
