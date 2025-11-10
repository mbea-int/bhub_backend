from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Follower, Subscriber
from notifications.models import Notification

@receiver(post_save, sender=Follower)
def notify_new_follower(sender, instance, created, **kwargs):
    """Notify business owner of new follower"""
    if created:
        Notification.create_notification(
            user=instance.business.user,
            notification_type='follow',
            title='New Follower',
            message=f'{instance.user.full_name} started following your business',
            related_type='business',
            related_id=instance.business.id
        )

@receiver(post_save, sender=Subscriber)
def notify_new_subscriber(sender, instance, created, **kwargs):
    """Notify business owner of new subscriber"""
    if created:
        Notification.create_notification(
            user=instance.business.user,
            notification_type='subscribe',
            title='New Subscriber',
            message=f'{instance.user.full_name} subscribed to your notifications',
            related_type='business',
            related_id=instance.business.id
        )