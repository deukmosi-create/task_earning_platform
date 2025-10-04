from .models import Notification
from .tasks import process_notification

def send_notification(user=None, user_type=None, title='', message='', notification_type='', data=None):
    """Utility function to send notifications"""
    if data is None:
        data = {}
    
    notification = Notification.objects.create(
        user=user,
        user_type=user_type,
        title=title,
        message=message,
        notification_type=notification_type,
        data=data
    )
    
    # Process notification asynchronously
    process_notification.delay(notification.id)
    
    return notification