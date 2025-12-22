import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Create Celery app
app = Celery('core')

# Load config from Django settings (with CELERY_ prefix)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Periodic tasks configuration
app.conf.beat_schedule = {
    'send-weekly-summary': {
        'task': 'projects.tasks.send_weekly_summary',
        'schedule': crontab(hour=9, minute=0, day_of_week='monday'),  # Every Monday at 9 AM
    },
    'cleanup-old-activities': {
        'task': 'projects.tasks.cleanup_old_activities',
        'schedule': crontab(hour=2, minute=0),  # Every day at 2 AM
    },
}

@app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery"""
    print(f'Request: {self.request!r}')