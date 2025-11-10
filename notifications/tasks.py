from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task
def send_email_notification(user_email, subject, message):
    """Send email notification asynchronously"""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )
        return f"Email sent to {user_email}"
    except Exception as e:
        return f"Failed to send email: {str(e)}"


@shared_task
def send_bulk_notification(user_ids, notification_type, title, message):
    """Send notification to multiple users"""
    from users.models import User
    from .models import Notification

    users = User.objects.filter(id__in=user_ids)
    created = 0

    for user in users:
        Notification.create_notification(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message
        )
        created += 1

    return f"Created {created} notifications"