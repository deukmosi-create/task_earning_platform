from celery import shared_task
from django.utils import timezone
from apps.users.models import EmailVerificationToken, PhoneVerificationToken
from apps.notifications.models import Notification

@shared_task
def cleanup_expired_tokens():
    """Clean up expired verification tokens"""
    now = timezone.now()
    
    # Delete expired email verification tokens
    expired_email_tokens = EmailVerificationToken.objects.filter(expires_at__lt=now)
    expired_email_tokens.delete()
    
    # Delete expired phone verification tokens
    expired_phone_tokens = PhoneVerificationToken.objects.filter(expires_at__lt=now)
    expired_phone_tokens.delete()
    
    return f"Cleaned up {expired_email_tokens.count() + expired_phone_tokens.count()} expired tokens"

@shared_task
def cleanup_old_notifications():
    """Clean up old notifications"""
    from datetime import timedelta
    cutoff_date = timezone.now() - timedelta(days=30)  # Keep 30 days of notifications
    
    old_notifications = Notification.objects.filter(created_at__lt=cutoff_date)
    count = old_notifications.count()
    old_notifications.delete()
    
    return f"Cleaned up {count} old notifications"