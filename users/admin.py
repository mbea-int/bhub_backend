from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, BlockedUser


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'full_name', 'user_type', 'is_email_verified', 'is_banned', 'created_at']
    list_filter = ['user_type', 'is_email_verified', 'is_banned', 'is_active', 'created_at']
    search_fields = ['email', 'full_name', 'phone']
    ordering = ['-created_at']

    fieldsets = (
        ('Account Info', {
            'fields': ('email', 'password', 'full_name', 'phone', 'bio', 'profile_image')
        }),
        ('Account Type', {
            'fields': ('user_type', 'is_email_verified', 'language', 'profile_visibility')
        }),
        ('Referral', {
            'fields': ('referral_code', 'referred_by')
        }),
        ('Moderation', {
            'fields': ('is_active', 'is_banned', 'ban_reason')
        }),
        ('Permissions', {
            'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Dates', {
            'fields': ('last_login', 'created_at', 'updated_at')
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'password1', 'password2', 'user_type', 'is_staff', 'is_superuser'),
        }),
    )

    readonly_fields = ['created_at', 'updated_at', 'last_login', 'referral_code']

    actions = ['ban_users', 'unban_users', 'verify_email']

    def ban_users(self, request, queryset):
        queryset.update(is_banned=True)
        self.message_user(request, f'{queryset.count()} users banned')

    ban_users.short_description = 'Ban selected users'

    def unban_users(self, request, queryset):
        queryset.update(is_banned=False, ban_reason=None)
        self.message_user(request, f'{queryset.count()} users unbanned')

    unban_users.short_description = 'Unban selected users'

    def verify_email(self, request, queryset):
        queryset.update(is_email_verified=True)
        self.message_user(request, f'{queryset.count()} emails verified')

    verify_email.short_description = 'Verify email for selected users'


@admin.register(BlockedUser)
class BlockedUserAdmin(admin.ModelAdmin):
    list_display = ['blocker', 'blocked', 'created_at']
    search_fields = ['blocker__email', 'blocked__email']
    date_hierarchy = 'created_at'