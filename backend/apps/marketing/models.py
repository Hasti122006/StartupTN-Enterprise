from django.db import models
from apps.companies.models import Company


class EmailCampaign(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]

    name = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    body = models.TextField(help_text="HTML or plain text campaign message content")
    
    # Targeting filters (optional)
    target_sector = models.CharField(max_length=255, null=True, blank=True, help_text="Filter companies by sector")
    target_stage = models.CharField(max_length=255, null=True, blank=True, help_text="Filter companies by stage")
    target_location = models.CharField(max_length=255, null=True, blank=True, help_text="Filter companies by location")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    scheduled_time = models.DateTimeField(null=True, blank=True, help_text="Time to send the email campaign automatically")
    
    sent_count = models.IntegerField(default=0)
    failed_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'email_campaigns'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class CampaignDelivery(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]

    campaign = models.ForeignKey(EmailCampaign, on_delete=models.CASCADE, related_name='deliveries')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='campaign_deliveries')
    email_address = models.CharField(max_length=500)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'campaign_deliveries'
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.campaign.name} to {self.email_address} ({self.status})"
