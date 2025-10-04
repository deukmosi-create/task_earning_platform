import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('task_earning_platform')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    'cleanup-expired-tokens': {
        'task': 'apps.users.tasks.cleanup_expired_tokens',
        'schedule': 3600.0,  # Every hour
    },
}