from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Notification
from apps.users.models import User

@shared_task
def send_email_notification(user_id, subject, message):
    """Async email notification"""
    try:
        user = User.objects.get(id=user_id)
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return f"Email sent to {user.email}"
    except User.DoesNotExist:
        return "User not found"

@shared_task
def send_sms_notification(phone_number, message):
    """Async SMS notification (implement with your SMS provider)"""
    # This would integrate with Twilio, AWS SNS, etc.
    print(f"SMS sent to {phone_number}: {message}")
    return f"SMS sent to {phone_number}"

@shared_task
def process_notification(notification_id):
    """Process a notification for all delivery methods"""
    try:
        notification = Notification.objects.get(id=notification_id)
        if notification.user:
            # Send email
            send_email_notification.delay(
                notification.user.id,
                notification.title,
                notification.message
            )
            
            # Send SMS if phone number exists
            if notification.user.phone_number:
                send_sms_notification.delay(
                    str(notification.user.phone_number),
                    notification.message
                )
        
        return f"Notification {notification_id} processed"
    except Notification.DoesNotExist:
        return "Notification not found"