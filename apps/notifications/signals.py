from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Notification
from .tasks import process_notification

@receiver(post_save, sender=Notification)
def notification_created(sender, instance, created, **kwargs):
    if created:
        process_notification.delay(instance.id)