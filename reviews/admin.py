from django.contrib import admin
from .models import Inquiry, Review


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ['post', 'buyer', 'seller', 'status', 'is_reviewed', 'created_at']
    list_filter = ['status', 'is_reviewed', 'created_at']
    search_fields = ['buyer__email', 'seller__email', 'post__product_name']
    date_hierarchy = 'created_at'


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['business', 'user', 'rating', 'is_approved', 'created_at']
    list_filter = ['rating', 'is_approved', 'created_at']
    search_fields = ['business__business_name', 'user__email', 'comment']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']

    actions = ['approve_reviews', 'disapprove_reviews']

    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f'{queryset.count()} reviews approved')

    approve_reviews.short_description = 'Approve selected reviews'

    def disapprove_reviews(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, f'{queryset.count()} reviews disapproved')

    disapprove_reviews.short_description = 'Disapprove selected reviews'