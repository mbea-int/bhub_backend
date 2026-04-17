import uuid
from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from datetime import timedelta
from users.models import User


class GroupManager(models.Manager):
    def active(self):
        return self.filter(is_active=True)


class Group(models.Model):
    CATEGORY_CHOICES = [
        ('books', 'Books & Reading'),
        ('recipes', 'Recipes & Cooking'),
        ('health', 'Health & Fitness'),
        ('education', 'Education & Learning'),
        ('parenting', 'Parenting & Family'),
        ('business', 'Business & Entrepreneurship'),
        ('community', 'Community Events'),
        ('general', 'General Discussion'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.URLField(max_length=500, blank=True, null=True)
    cover_image = models.URLField(max_length=500, blank=True, null=True)
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES, default='general')

    # Settings
    require_approval = models.BooleanField(default=True, help_text="Require admin approval for new members")
    max_images_per_post = models.IntegerField(default=5, help_text="Maximum images allowed per post")
    max_videos_per_post = models.IntegerField(default=2, help_text="Maximum videos allowed per post")
    message_retention_days = models.IntegerField(default=90, help_text="Days to keep messages")

    # Stats
    total_members = models.IntegerField(default=0)
    total_posts = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_groups')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = GroupManager()

    class Meta:
        db_table = 'groups'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            counter = 1
            original_slug = self.slug
            while Group.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    @property
    def admins(self):
        return self.members.filter(role='admin')

    @property
    def moderators(self):
        return self.members.filter(role='moderator')


class GroupMember(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('moderator', 'Moderator'),
        ('member', 'Member'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('banned', 'Banned'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # For banned members
    banned_reason = models.TextField(blank=True, null=True)
    banned_at = models.DateTimeField(blank=True, null=True)
    banned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='banned_members')

    joined_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'group_members'
        unique_together = ['group', 'user']
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user.email} in {self.group.name} ({self.role})"

    def is_admin(self):
        return self.role == 'admin' and self.status == 'approved'

    def is_moderator(self):
        return self.role in ['admin', 'moderator'] and self.status == 'approved'


class GroupJoinRequest(models.Model):
    """Separate model for join requests to track approval flow"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='join_requests')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_join_requests')
    message = models.TextField(blank=True, null=True, help_text="Optional message to admin")
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='pending')

    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='reviewed_requests')
    reviewed_at = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'group_join_requests'
        unique_together = ['group', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} -> {self.group.name} ({self.status})"


class GroupPost(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='posts')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_posts')
    content = models.TextField()
    images = models.JSONField(default=list, blank=True)  # Array of image URLs
    videos = models.JSONField(default=list, blank=True)  # Array of video URLs

    total_likes = models.IntegerField(default=0)
    total_comments = models.IntegerField(default=0)
    is_pinned = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)

    # For moderation
    is_deleted = models.BooleanField(default=False)
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deleted_posts')
    deleted_at = models.DateTimeField(blank=True, null=True)
    deletion_reason = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'group_posts'
        ordering = ['-is_pinned', '-created_at']
        indexes = [
            models.Index(fields=['group', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"Post in {self.group.name} by {self.user.full_name}"

    def soft_delete(self, deleted_by, reason=None):
        """Soft delete post"""
        self.is_deleted = True
        self.deleted_by = deleted_by
        self.deleted_at = timezone.now()
        self.deletion_reason = reason
        self.save()


class GroupComment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group_post = models.ForeignKey(GroupPost, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_comments')
    content = models.TextField()
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')

    is_deleted = models.BooleanField(default=False)
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='deleted_comments')
    deleted_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'group_comments'
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.user.full_name}"


class GroupPostLike(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group_post = models.ForeignKey(GroupPost, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='liked_group_posts')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'group_post_likes'
        unique_together = ['group_post', 'user']
        ordering = ['-created_at']


class GroupMessage(models.Model):
    """Messages within a group - with retention policy"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_group_messages')
    content = models.TextField()
    images = models.JSONField(default=list, blank=True)

    expires_at = models.DateTimeField()
    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'group_messages'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['group', '-created_at']),
            models.Index(fields=['expires_at']),
        ]

    def save(self, *args, **kwargs):
        if not self.expires_at:
            retention_days = self.group.message_retention_days
            self.expires_at = timezone.now() + timedelta(days=retention_days)
        super().save(*args, **kwargs)

    @classmethod
    def cleanup_expired_messages(cls):
        """Clean up expired messages"""
        expired = cls.objects.filter(expires_at__lt=timezone.now())
        count = expired.count()
        expired.delete()
        return count

    def __str__(self):
        return f"Message in {self.group.name} by {self.sender.full_name}"