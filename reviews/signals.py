from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Inquiry, Review
from notifications.models import Notification

@receiver(post_save, sender=Inquiry)
def notify_inquiry_created(sender, instance, created, **kwargs):
    """Notify seller when inquiry is created"""
    if created:
        Notification.create_notification(
            user=instance.seller,
            notification_type='inquiry',
            title='New Inquiry',
            message=f'{instance.buyer.full_name} is interested in {instance.post.product_name}',
            related_type='inquiry',
            related_id=instance.id
        )

@receiver(post_save, sender=Review)
def notify_review_created(sender, instance, created, **kwargs):
    """Notify business owner when review is created"""
    if created:
        Notification.create_notification(
            user=instance.business.user,
            notification_type='review',
            title='New Review',
            message=f'{instance.user.full_name} left a {instance.rating}-star review',
            related_type='business',
            related_id=instance.business.id
        )