from django.contrib import admin
from .models import Post, PostLike, SavedPost, PostDailyLimit


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'business', 'category', 'price', 'is_available', 'is_featured', 'total_views',
                    'total_likes', 'created_at']
    list_filter = ['category', 'is_available', 'is_featured', 'created_at']
    search_fields = ['product_name', 'description', 'business__business_name']
    ordering = ['-created_at']
    readonly_fields = ['total_likes', 'total_inquiries', 'total_views', 'created_at', 'updated_at']

    actions = ['mark_featured', 'unmark_featured', 'mark_unavailable']

    def mark_featured(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, f'{queryset.count()} posts marked as featured')

    mark_featured.short_description = 'Mark as featured'

    def unmark_featured(self, request, queryset):
        queryset.update(is_featured=False)
        self.message_user(request, f'{queryset.count()} posts unmarked as featured')

    unmark_featured.short_description = 'Remove featured status'

    def mark_unavailable(self, request, queryset):
        queryset.update(is_available=False)
        self.message_user(request, f'{queryset.count()} posts marked as unavailable')

    mark_unavailable.short_description = 'Mark as unavailable'


@admin.register(PostDailyLimit)
class PostDailyLimitAdmin(admin.ModelAdmin):
    list_display = ['business', 'date', 'posts_count']
    list_filter = ['date']
    search_fields = ['business__business_name']
    date_hierarchy = 'date'