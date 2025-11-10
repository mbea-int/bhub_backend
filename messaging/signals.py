from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message
from notifications.models import Notification

@receiver(post_save, sender=Message)
def notify_new_message(sender, instance, created, **kwargs):
    """Notify receiver of new message"""
    if created:
        Notification.create_notification(
            user=instance.receiver,
            notification_type='message',
            title='New Message',
            message=f'{instance.sender.full_name} sent you a message',
            related_type='message',
            related_id=instance.id
        )