"""
Celery configuration for Disha LMS.
T173: Install and configure Celery
"""

import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

# Create Celery app
app = Celery('disha_lms')

# Load config from Django settings with CELERY namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery."""
    print(f'Request: {self.request!r}')


# Celery Beat Schedule for periodic tasks
app.conf.beat_schedule = {
    # Example: Send pending surveys every day at 9 AM
    'send-pending-surveys': {
        'task': 'apps.feedback.tasks.send_pending_surveys',
        'schedule': crontab(hour=9, minute=0),
    },
    # Example: Send survey reminders every day at 5 PM
    'send-survey-reminders': {
        'task': 'apps.feedback.tasks.send_survey_reminders',
        'schedule': crontab(hour=17, minute=0),
    },
}
