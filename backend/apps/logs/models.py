from django.db import models
from apps.jobs.models import Job


class Log(models.Model):
    LEVEL_CHOICES = (
        ('DEBUG', 'DEBUG'),
        ('INFO', 'INFO'),
        ('WARNING', 'WARNING'),
        ('ERROR', 'ERROR'),
        ('CRITICAL', 'CRITICAL'),
    )

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='logs'
    )
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='INFO', db_index=True)
    message = models.TextField()
    page = models.PositiveIntegerField(null=True, blank=True)
    company = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.level}] {self.message[:50]}"
