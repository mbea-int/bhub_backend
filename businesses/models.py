import os
import uuid
from django.db import models
from django.utils.text import slugify
from users.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

def business_logo_path(instance, filename):
    """Generate unique path for business logos"""
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return os.path.join('businesses/logos', filename)

class BusinessManager(models.Manager):
    def active(self):
        return self.filter(user__is_active=True, user__is_banned=False)

    def verified(self):
        return self.active().filter(is_verified=True)

    def premium(self):
        return self.verified().filter(is_premium=True)


class BusinessCategory(models.Model):
    """
    Zgjedhjet e ikonave të Material Icons për Flutter.
    Çdo kategori mund të ketë ikonën e saj specifike.
    """
    ICON_CHOICES = [
        # Food & Dining
        ('restaurant_rounded', 'Restaurant'),
        ('local_cafe_rounded', 'Cafe'),
        ('bakery_dining_rounded', 'Bakery'),
        ('local_pizza_rounded', 'Pizza'),
        ('lunch_dining_rounded', 'Fast Food'),
        ('ramen_dining_rounded', 'Ramen/Noodles'),

        # Shopping & Retail
        ('store_rounded', 'Store/Market'),
        ('storefront_rounded', 'Shop/Butcher'),
        ('checkroom_rounded', 'Clothing Store'),
        ('shopping_bag_rounded', 'Shopping'),
        ('shopping_cart_rounded', 'Supermarket'),

        # Services
        ('content_cut_rounded', 'Barbershop'),
        ('face_rounded', 'Beauty/Salon'),
        ('spa_rounded', 'Spa'),
        ('cleaning_services_rounded', 'Cleaning'),
        ('build_rounded', 'Construction/Repair'),
        ('plumbing_rounded', 'Plumbing'),
        ('electrical_services_rounded', 'Electrical'),

        # Healthcare
        ('local_hospital_rounded', 'Hospital/Clinic'),
        ('local_pharmacy_rounded', 'Pharmacy'),
        ('medical_services_rounded', 'Medical Services'),
        ('dental_services_rounded', 'Dental'),
        ('psychology_rounded', 'Psychology'),

        # Education & Religion
        ('school_rounded', 'School/Education'),
        ('mosque_rounded', 'Mosque'),
        ('menu_book_rounded', 'Library/Books'),
        ('science_rounded', 'Science/Lab'),

        # Travel & Hospitality
        ('flight_rounded', 'Travel Agency'),
        ('hotel_rounded', 'Hotel'),
        ('apartment_rounded', 'Apartment/Real Estate'),
        ('directions_car_rounded', 'Car Services'),
        ('local_taxi_rounded', 'Taxi'),

        # Fitness & Sports
        ('fitness_center_rounded', 'Gym/Fitness'),
        ('sports_soccer_rounded', 'Sports'),
        ('pool_rounded', 'Swimming'),

        # Technology & Electronics
        ('computer_rounded', 'Computer/Tech'),
        ('phone_android_rounded', 'Mobile/Electronics'),
        ('camera_rounded', 'Photography'),

        # Entertainment
        ('movie_rounded', 'Cinema/Entertainment'),
        ('theater_comedy_rounded', 'Theater'),
        ('music_note_rounded', 'Music'),

        # Default
        ('business_rounded', 'Default Business'),
        ('business_center_rounded', 'Business Center'),
        ('store_mall_directory_rounded', 'Mall/Directory'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    icon = models.CharField(
        max_length=50,
        choices=ICON_CHOICES,
        default='business_rounded',
        blank=True,
        null=True,
        help_text='Material Icon name for Flutter app'
    )
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'business_categories'
        verbose_name = 'Business Category'
        verbose_name_plural = 'Business Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        # Nëse nuk ka icon, vendos default
        if not self.icon:
            self.icon = 'business_rounded'
        super().save(*args, **kwargs)

class Business(models.Model):
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

    VERIFICATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='businesses')
    business_name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField()
    category = models.ForeignKey(
        BusinessCategory,
        on_delete=models.PROTECT,
        related_name='businesses'
    )
    # to identify main business
    is_primary = models.BooleanField(default=False)
    logo = models.URLField(max_length=500, blank=True, null=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    address = models.TextField()
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Albania')

    latitude = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, blank=True, null=True)

    business_hours = models.JSONField(blank=True, null=True)
    is_open_now = models.BooleanField(default=False)

    is_verified = models.BooleanField(default=False)
    verification_documents = models.JSONField(blank=True, null=True)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='pending')
    verification_date = models.DateTimeField(blank=True, null=True)

    is_premium = models.BooleanField(default=False)
    premium_until = models.DateTimeField(blank=True, null=True)

    max_posts_per_day = models.IntegerField(default=3, validators=[MinValueValidator(1)])

    total_followers = models.IntegerField(default=0)
    total_subscribers = models.IntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('0.00'),
                                         validators=[MinValueValidator(0), MaxValueValidator(5)])
    total_reviews = models.IntegerField(default=0)

    is_halal_certified = models.BooleanField(default=False)
    halal_certificate = models.URLField(max_length=500, blank=True, null=True)

    social_instagram = models.CharField(max_length=255, blank=True, null=True)
    social_facebook = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = BusinessManager()

    class Meta:
        db_table = 'businesses'
        ordering = ['-created_at']
        verbose_name_plural = 'Businesses'
        # Add constraint to ensure only one primary business per user
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=models.Q(is_primary=True),
                name='unique_primary_business_per_user'
            )
        ]

    def __str__(self):
        return self.business_name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.business_name)
            # Ensure uniqueness
            counter = 1
            original_slug = self.slug
            while Business.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        # Auto-set as primary if it's the user's first business
        if not self.pk and not self.user.businesses.exists():
            self.is_primary = True

            # ✅ Ensure only one primary business per user
        if self.is_primary:
            Business.objects.filter(user=self.user, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

    @property
    def category_name(self):
        """Get category name for backward compatibility"""
        return self.category.name if self.category else None

    @property
    def category_slug(self):
        """Get category slug"""
        return self.category.slug if self.category else None

    def is_within_post_limit(self):
        """Check if business can post today"""
        from django.utils import timezone
        from posts.models import PostDailyLimit

        today = timezone.now().date()
        limit, created = PostDailyLimit.objects.get_or_create(
            business=self,
            date=today,
            defaults={'posts_count': 0}
        )
        return limit.posts_count < self.max_posts_per_day

    def calculate_average_rating(self):
        """Recalculate average rating from reviews"""
        from django.db.models import Avg
        from reviews.models import Review

        result = Review.objects.filter(business=self, is_approved=True).aggregate(Avg('rating'))
        self.average_rating = result['rating__avg'] or Decimal('0.00')
        self.total_reviews = Review.objects.filter(business=self, is_approved=True).count()
        self.save()


class Follower(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='followers')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'followers'
        unique_together = ['business', 'user']
        ordering = ['-created_at']


class Subscriber(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='subscribers')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    notification_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'subscribers'
        unique_together = ['business', 'user']
        ordering = ['-created_at']


class BusinessAnalytics(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='analytics')
    date = models.DateField()
    profile_views = models.IntegerField(default=0)
    post_views = models.IntegerField(default=0)
    total_clicks = models.IntegerField(default=0)
    total_inquiries = models.IntegerField(default=0)
    total_followers_gained = models.IntegerField(default=0)

    class Meta:
        db_table = 'business_analytics'
        unique_together = ['business', 'date']
        ordering = ['-date']