from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import GroupPost, GroupComment, GroupMember
from notifications.models import Notification


@receiver(post_save, sender=GroupPost)
def notify_group_post(sender, instance, created, **kwargs):
    """Notify group members of new post"""
    if created:
        # Get all group members except the post author
        members = GroupMember.objects.filter(group=instance.group).exclude(user=instance.user)

        for member in members:
            Notification.create_notification(
                user=member.user,
                notification_type='group',
                title=f'New post in {instance.group.name}',
                message=f'{instance.user.full_name} posted in {instance.group.name}',
                related_type='group_post',
                related_id=instance.id
            )


@receiver(post_save, sender=GroupComment)
def notify_comment(sender, instance, created, **kwargs):
    """Notify post author of new comment"""
    if created:
        # Notify post author
        if instance.group_post.user != instance.user:
            Notification.create_notification(
                user=instance.group_post.user,
                notification_type='group',
                title='New Comment',
                message=f'{instance.user.full_name} commented on your post',
                related_type='group_post',
                related_id=instance.group_post.id
            )