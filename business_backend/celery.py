import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'business_backend.settings')

app = Celery('muslim_community')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Celery Beat Schedule
app.conf.beat_schedule = {
    # Reset daily post limits at midnight
    'reset-daily-post-limits': {
        'task': 'apps.posts.tasks.reset_daily_post_limits',
        'schedule': crontab(hour=0, minute=0),
    },
    # Update business open/closed status every hour
    'update-business-hours': {
        'task': 'apps.businesses.tasks.update_business_open_status',
        'schedule': crontab(minute=0),
    },
    # Calculate daily analytics
    'calculate-daily-analytics': {
        'task': 'apps.businesses.tasks.calculate_daily_analytics',
        'schedule': crontab(hour=1, minute=0),
    },
    # Check premium expiry
    'check-premium-expiry': {
        'task': 'apps.businesses.tasks.check_premium_expiry',
        'schedule': crontab(hour=2, minute=0),
    },
    # Send premium expiry reminders (3 days before)
    'send-premium-reminders': {
        'task': 'apps.businesses.tasks.send_premium_expiry_reminders',
        'schedule': crontab(hour=9, minute=0),
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')