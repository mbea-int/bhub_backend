from celery import shared_task
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Business, BusinessAnalytics
from notifications.models import Notification


@shared_task
def update_business_open_status():
    """Update is_open_now status for all businesses"""
    now = timezone.now()
    current_day = now.strftime('%A').lower()
    current_time = now.strftime('%H:%M')

    businesses = Business.objects.filter(business_hours__isnull=False)
    updated = 0

    for business in businesses:
        hours = business.business_hours.get(current_day)
        if hours:
            # Parse hours (e.g., "09:00-22:00")
            try:
                open_time, close_time = hours.split('-')
                is_open = open_time <= current_time <= close_time

                if business.is_open_now != is_open:
                    business.is_open_now = is_open
                    business.save(update_fields=['is_open_now'])
                    updated += 1
            except:
                pass

    return f"Updated {updated} businesses"


@shared_task
def calculate_daily_analytics():
    """Calculate and store daily analytics for all businesses"""
    yesterday = timezone.now().date() - timedelta(days=1)
    businesses = Business.objects.all()

    for business in businesses:
        # TODO: Calculate actual analytics from views/clicks/etc
        BusinessAnalytics.objects.get_or_create(
            business=business,
            date=yesterday,
            defaults={
                'profile_views': 0,
                'post_views': 0,
                'total_clicks': 0,
                'total_inquiries': 0,
                'total_followers_gained': 0,
            }
        )

    return f"Calculated analytics for {businesses.count()} businesses"


@shared_task
def check_premium_expiry():
    """Check and disable expired premium subscriptions"""
    now = timezone.now()
    expired = Business.objects.filter(
        is_premium=True,
        premium_until__lt=now
    )

    count = expired.update(is_premium=False)
    return f"Disabled {count} expired premium subscriptions"


@shared_task
def send_premium_expiry_reminders():
    """Send reminders to businesses whose premium expires in 3 days"""
    reminder_date = timezone.now() + timedelta(days=3)
    businesses = Business.objects.filter(
        is_premium=True,
        premium_until__date=reminder_date.date()
    )

    for business in businesses:
        Notification.create_notification(
            user=business.user,
            notification_type='admin',
            title='Premium Subscription Expiring Soon',
            message=f'Your premium subscription expires in 3 days. Renew now to continue enjoying premium benefits.',
            related_type='business',
            related_id=business.id
        )

        # TODO: Send email notification

    return f"Sent {businesses.count()} premium expiry reminders"