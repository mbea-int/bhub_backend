import uuid
from django.db import models
from users.models import User


class Report(models.Model):
    TYPE_CHOICES = [
        ('user', 'User'),
        ('business', 'Business'),
        ('post', 'Post'),
        ('group_post', 'Group Post'),
        ('comment', 'Comment'),
    ]

    REASON_CHOICES = [
        ('spam', 'Spam'),
        ('inappropriate', 'Inappropriate Content'),
        ('harassment', 'Harassment'),
        ('fake', 'Fake/Misleading'),
        ('violence', 'Violence'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewing', 'Under Review'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    reported_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    reported_id = models.UUIDField()

    reason = models.CharField(max_length=100, choices=REASON_CHOICES)
    description = models.TextField(blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_note = models.TextField(blank=True, null=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='reports_resolved')
    resolved_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reports'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reported_type', 'reported_id']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f"Report: {self.reported_type} by {self.reporter.email}"