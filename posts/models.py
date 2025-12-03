import uuid
from django.db import models
from businesses.models import Business, BusinessCategory
from users.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class PostManager(models.Manager):
    def available(self):
        return self.filter(is_available=True, business__user__is_active=True)


class ProductCategory(models.Model):
    """
    Kategoritë e produkteve/shërbimeve që krijohen nga bizneset.
    Çdo biznes mund të krijojë kategoritë e veta.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='product_categories'
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=150, blank=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True, help_text='Material Icon name')
    display_order = models.IntegerField(default=0, help_text='Order for displaying categories')
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'product_categories'
        ordering = ['display_order', 'name']
        unique_together = ['business', 'slug']
        verbose_name = 'Product Category'
        verbose_name_plural = 'Product Categories'
        indexes = [
            models.Index(fields=['business', 'is_active']),
        ]

    def __str__(self):
        return f"{self.business.business_name} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.name)
            self.slug = base_slug
            counter = 1
            while ProductCategory.objects.filter(
                    business=self.business,
                    slug=self.slug
            ).exclude(pk=self.pk).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    @property
    def posts_count(self):
        """Number of active posts in this category"""
        return self.posts.filter(is_available=True).count()


class Post(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='posts')

    # Kategoria e biznesit (Food, Fashion, etc.)
    business_category = models.ForeignKey(
        BusinessCategory,
        on_delete=models.PROTECT,
        related_name='posts',
        help_text='Main business category (Food, Fashion, etc.)'
    )

    # Kategoria e produktit (Bluza, Xhaketa, etc.) - OPSIONALE
    product_category = models.ForeignKey(
        ProductCategory,
        on_delete=models.SET_NULL,
        related_name='posts',
        blank=True,
        null=True,
        help_text='Specific product category created by business'
    )

    product_name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )

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
            models.Index(fields=['business_category', '-created_at']),
            models.Index(fields=['product_category', '-created_at']),
            models.Index(fields=['is_featured', '-created_at']),
            models.Index(fields=['business', 'product_category', '-created_at']),
        ]

    def __str__(self):
        return f"{self.product_name} - {self.business.business_name}"

    def clean(self):
        """Validate that product_category belongs to the same business"""
        from django.core.exceptions import ValidationError
        if self.product_category and self.product_category.business != self.business:
            raise ValidationError(
                'Product category must belong to the same business.'
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

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