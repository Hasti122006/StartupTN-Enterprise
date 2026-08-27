import logging
import threading
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from django.conf import settings
from celery import shared_task

logger = logging.getLogger(__name__)


def run_campaign_sending(campaign_id):
    """
    Main business logic for campaign sending.
    This can be called from either a Celery task or a background thread fallback.
    """
    from .models import EmailCampaign, CampaignDelivery
    from apps.companies.models import Company
    
    try:
        campaign = EmailCampaign.objects.get(id=campaign_id)
    except EmailCampaign.DoesNotExist:
        logger.error(f"[MARKETING] Campaign #{campaign_id} not found")
        return f"Campaign #{campaign_id} not found"

    # Avoid duplicate sends unless in debug/dev
    if campaign.status in ['sending', 'sent'] and not getattr(settings, 'DEBUG', False):
        return f"Campaign #{campaign_id} already sent or sending"

    campaign.status = 'sending'
    campaign.save(update_fields=['status'])

    # Build company queryset based on target criteria
    companies = Company.objects.exclude(email__isnull=True).exclude(email='')
    
    if campaign.target_sector:
        companies = companies.filter(sector__icontains=campaign.target_sector)
    if campaign.target_stage:
        companies = companies.filter(current_stage__iexact=campaign.target_stage)
    if campaign.target_location:
        companies = companies.filter(location__icontains=campaign.target_location)

    sent_count = 0
    failed_count = 0
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@startuptn.in')

    for company in companies:
        email_addr = company.email.strip()
        if not email_addr:
            continue

        # Create delivery record
        delivery = CampaignDelivery.objects.create(
            campaign=campaign,
            company=company,
            email_address=email_addr,
            status='pending'
        )

        try:
            # Personalize the email content (subject and body)
            subject_personalized = campaign.subject.replace('{company_name}', company.company_name or '')
            body_personalized = campaign.body.replace('{company_name}', company.company_name or '')
            
            founders_str = company.founders
            if not founders_str or not founders_str.strip():
                founders_str = "Founder"
            
            subject_personalized = subject_personalized.replace('{founders}', founders_str)
            body_personalized = body_personalized.replace('{founders}', founders_str)
            
            text_content = strip_tags(body_personalized)
            
            msg = EmailMultiAlternatives(
                subject=subject_personalized,
                body=text_content,
                from_email=from_email,
                to=[email_addr]
            )
            msg.attach_alternative(body_personalized, "text/html")
            msg.send()

            delivery.status = 'sent'
            delivery.sent_at = timezone.now()
            delivery.save(update_fields=['status', 'sent_at'])
            sent_count += 1
        except Exception as e:
            logger.exception(f"[MARKETING] Failed to send to {email_addr} for campaign #{campaign_id}")
            delivery.status = 'failed'
            delivery.error_message = str(e)
            delivery.save(update_fields=['status', 'error_message'])
            failed_count += 1

    campaign.status = 'sent' if failed_count == 0 else 'failed'
    campaign.sent_count = sent_count
    campaign.failed_count = failed_count
    campaign.save(update_fields=['status', 'sent_count', 'failed_count', 'updated_at'])

    return f"Campaign #{campaign_id} sending complete. Success: {sent_count}, Failed: {failed_count}"


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def send_campaign_task(self, campaign_id):
    """Celery task to send campaign emails."""
    try:
        return run_campaign_sending(campaign_id)
    except Exception as exc:
        logger.exception(f"[MARKETING] Exception in Celery task for campaign #{campaign_id}")
        raise self.retry(exc=exc)


@shared_task
def check_and_run_scheduled_campaigns():
    """Periodic checker for scheduled campaigns that need to run."""
    from .models import EmailCampaign
    now = timezone.now()
    scheduled = EmailCampaign.objects.filter(status='scheduled', scheduled_time__lte=now)
    
    count = 0
    for campaign in scheduled:
        trigger_campaign_send(campaign.id)
        count += 1
    return f"Scheduled scan complete. Triggered {count} campaigns."


def trigger_campaign_send(campaign_id):
    """
    Triggers campaign sending asynchronously.
    Prefers Celery, but falls back to a Python background thread if Celery is unavailable.
    """
    try:
        # Attempt to queue via Celery
        send_campaign_task.delay(campaign_id)
        logger.info(f"[MARKETING] Dispatched campaign #{campaign_id} via Celery")
    except Exception as e:
        logger.warning(f"[MARKETING] Celery dispatch failed ({e}). Falling back to background thread.")
        # Fallback thread execution
        thread = threading.Thread(
            target=run_campaign_sending,
            args=(campaign_id,),
            name=f"CampaignSender-{campaign_id}"
        )
        thread.daemon = True
        thread.start()
