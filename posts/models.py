import uuid
from django.db import models
from businesses.models import Business
from users.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class PostManager(models.Manager):
    def available(self):
        return self.filter(is_available=True, business__user__is_active=True)


class Post(models.Model):
    CATEGORY_CHOICES = [
        ('food', 'Food & Restaurants'),
        ('fashion', 'Fashion & Clothing'),
        ('books', 'Books & Education'),
        ('health', 'Health & Wellness'),
        ('education', 'Education & Training'),
        ('services', 'Services'),
        ('electronics', 'Electronics'),
        ('home', 'Home & Garden'),
        ('beauty', 'Beauty & Personal Care'),
        ('sports', 'Sports & Fitness'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='posts')
    product_name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)

    image_url = models.URLField(max_length=500)
    image_thumbnail = models.URLField(max_length=500, blank=True, null=True)

    is_available = models.BooleanField(default=True)
    total_likes = models.IntegerField(default=0)
    total_inquiries = models.IntegerField(default=0)
    total_views = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=False)

    auto_share_instagram = models.BooleanField(default=False)
    auto_share_facebook = models.BooleanField(default=False)
    shared_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PostManager()

    class Meta:
        db_table = 'posts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['is_featured', '-created_at']),
        ]

    def __str__(self):
        return f"{self.product_name} - {self.business.business_name}"

    def increment_views(self):
        """Atomic increment of views"""
        from django.db.models import F
        Post.objects.filter(pk=self.pk).update(total_views=F('total_views') + 1)
        self.refresh_from_db()


class PostLike(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='liked_posts')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'post_likes'
        unique_together = ['post', 'user']
        ordering = ['-created_at']


class SavedPost(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='saved_by')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_posts')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'saved_posts'
        unique_together = ['post', 'user']
        ordering = ['-created_at']


class PostDailyLimit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='daily_limits')
    date = models.DateField()
    posts_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'post_daily_limits'
        unique_together = ['business', 'date']
        ordering = ['-date']