from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from .models import Business, BusinessCategory, Follower, Subscriber, BusinessAnalytics


@admin.register(BusinessCategory)
class BusinessCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            total_businesses=Count('businesses')
        )

@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'user_email', 'category', 'city', 'is_verified', 'is_premium', 'average_rating',
                    'total_followers']
    list_filter = ['category', 'city', 'is_verified', 'is_premium', 'verification_status', 'created_at']
    search_fields = ['business_name', 'user__email', 'city', 'phone']
    ordering = ['-created_at']
    readonly_fields = ['slug', 'total_followers', 'total_subscribers', 'average_rating', 'total_reviews', 'created_at',
                       'updated_at']

    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'business_name', 'slug', 'description', 'category', 'logo', 'logo_public_id')
        }),
        ('Contact', {
            'fields': ('phone', 'email', 'address', 'city', 'country')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude')
        }),
        ('Hours', {
            'fields': ('business_hours', 'is_open_now')
        }),
        ('Verification', {
            'fields': ('is_verified', 'verification_status', 'verification_documents', 'verification_date')
        }),
        ('Premium', {
            'fields': ('is_premium', 'premium_until', 'max_posts_per_day')
        }),
        ('Stats', {
            'fields': ('total_followers', 'total_subscribers', 'average_rating', 'total_reviews')
        }),
        ('Certification', {
            'fields': ('is_halal_certified', 'halal_certificate')
        }),
        ('Social', {
            'fields': ('social_instagram', 'social_facebook')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    actions = ['verify_businesses', 'reject_businesses', 'make_premium', 'remove_premium']

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = 'Owner Email'

    def verify_businesses(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_verified=True, verification_status='approved', verification_date=timezone.now())
        self.message_user(request, f'{queryset.count()} businesses verified')

    verify_businesses.short_description = 'Verify selected businesses'

    def reject_businesses(self, request, queryset):
        queryset.update(is_verified=False, verification_status='rejected')
        self.message_user(request, f'{queryset.count()} businesses rejected')

    reject_businesses.short_description = 'Reject selected businesses'

    def make_premium(self, request, queryset):
        from django.utils import timezone
        from datetime import timedelta
        queryset.update(is_premium=True, premium_until=timezone.now() + timedelta(days=30))
        self.message_user(request, f'{queryset.count()} businesses made premium')

    make_premium.short_description = 'Make selected businesses premium (30 days)'

    def remove_premium(self, request, queryset):
        queryset.update(is_premium=False, premium_until=None)
        self.message_user(request, f'{queryset.count()} businesses removed from premium')

    remove_premium.short_description = 'Remove premium status'


@admin.register(Follower)
class FollowerAdmin(admin.ModelAdmin):
    list_display = ['business', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['business__business_name', 'user__email']
    date_hierarchy = 'created_at'


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ['business', 'user', 'notification_enabled', 'created_at']
    list_filter = ['notification_enabled', 'created_at']
    search_fields = ['business__business_name', 'user__email']
    date_hierarchy = 'created_at'


@admin.register(BusinessAnalytics)
class BusinessAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['business', 'date', 'profile_views', 'post_views', 'total_clicks', 'total_inquiries']
    list_filter = ['date']
    search_fields = ['business__business_name']
    date_hierarchy = 'date'