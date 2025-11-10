import uuid
from django.db import models
from users.models import User


class Notification(models.Model):
    TYPE_CHOICES = [
        ('inquiry', 'Inquiry Received'),
        ('review', 'Review Added'),
        ('follow', 'New Follower'),
        ('subscribe', 'New Subscriber'),
        ('admin', 'Admin Message'),
        ('group', 'Group Activity'),
        ('message', 'New Message'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    message = models.TextField()

    related_type = models.CharField(max_length=50, blank=True, null=True)  # 'post', 'business', 'inquiry', etc.
    related_id = models.UUIDField(blank=True, null=True)

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
        ]

    def __str__(self):
        return f"{self.type} for {self.user.email}"

    @classmethod
    def create_notification(cls, user, notification_type, title, message, related_type=None, related_id=None):
        """Helper method to create notification"""
        return cls.objects.create(
            user=user,
            type=notification_type,
            title=title,
            message=message,
            related_type=related_type,
            related_id=related_id
        )