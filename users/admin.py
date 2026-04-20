from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils import timezone
from .models import User, BlockedUser, OAuthToken


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        'email', 'username', 'full_name', 'user_type',
        'is_email_verified', 'is_guest', 'is_banned', 'is_active', 'created_at'
    ]
    list_filter = [
        'user_type', 'is_email_verified', 'is_guest',
        'is_banned', 'is_active', 'language', 'profile_visibility',
    ]
    search_fields = ['email', 'username', 'full_name', 'phone', 'referral_code']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    readonly_fields = [
        'id', 'referral_code', 'created_at', 'updated_at',
        'last_login', 'username_changed_at', 'username_change_status'
    ]

    fieldsets = (
        ('Kredencialet', {
            'fields': ('id', 'email', 'password')
        }),
        ('Username', {
            'fields': ('username', 'username_changed_at', 'username_change_status'),
            'description': 'Username unik — mund të ndryshohet 1 herë në 30 ditë nga përdoruesi.'
        }),
        ('Informacioni Personal', {
            'fields': ('full_name', 'phone', 'bio', 'profile_image')
        }),
        ('Tipi & Statusi', {
            'fields': (
                'user_type', 'is_active', 'is_staff', 'is_superuser',
                'is_email_verified', 'email_verification_token',
                'language', 'profile_visibility',
            )
        }),
        ('Guest', {
            'fields': ('is_guest', 'guest_expires_at'),
            'classes': ('collapse',)
        }),
        ('Moderim', {
            'fields': ('is_banned', 'ban_reason'),
        }),
        ('Referral', {
            'fields': ('referral_code', 'referred_by'),
            'classes': ('collapse',)
        }),
        ('Permissions', {
            'fields': ('groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'username', 'full_name',
                'password1', 'password2',
                'user_type', 'is_staff', 'is_superuser'
            ),
        }),
    )

    actions = ['ban_users', 'unban_users', 'verify_email', 'reset_username_cooldown']

    # ── Custom display methods ──────────────────────────────────────────

    def username_change_status(self, obj):
        """Tregon sa ditë kanë mbetur për ndryshim username."""
        if not obj.username_changed_at:
            return format_html(
                '<span style="color: green;">✔ Mund të ndryshohet</span>'
            )
        days_since = (timezone.now() - obj.username_changed_at).days
        if days_since >= 30:
            return format_html(
                '<span style="color: green;">✔ Mund të ndryshohet</span>'
            )
        remaining = 30 - days_since
        return format_html(
            '<span style="color: orange;">⏳ {} ditë të mbetura</span>',
            remaining
        )
    username_change_status.short_description = 'Statusi i ndryshimit'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('referred_by')

    # ── Admin actions ───────────────────────────────────────────────────

    @admin.action(description='🚫 Blloko përdoruesit e zgjedhur')
    def ban_users(self, request, queryset):
        # Mos blloko superuserët
        protected = queryset.filter(is_superuser=True).count()
        updated = queryset.exclude(is_superuser=True).update(is_banned=True)
        msg = f'{updated} përdorues u bllokuan.'
        if protected:
            msg += f' {protected} superuser u anashkaluan.'
        self.message_user(request, msg)

    @admin.action(description='✅ Zhblloko përdoruesit e zgjedhur')
    def unban_users(self, request, queryset):
        updated = queryset.update(is_banned=False, ban_reason=None)
        self.message_user(request, f'{updated} përdorues u zhbllokuan.')

    @admin.action(description='✉️ Verifiko email për të zgjedhurit')
    def verify_email(self, request, queryset):
        updated = queryset.update(
            is_email_verified=True,
            email_verification_token=None
        )
        self.message_user(request, f'{updated} email u verifikuan.')

    @admin.action(description='🔄 Reseto kufizimin e username (30 ditë)')
    def reset_username_cooldown(self, request, queryset):
        updated = queryset.update(username_changed_at=None)
        self.message_user(
            request,
            f'{updated} përdorues mund të ndryshojnë username tani.'
        )


@admin.register(BlockedUser)
class BlockedUserAdmin(admin.ModelAdmin):
    list_display = ['blocker_email', 'blocked_email', 'created_at']
    search_fields = ['blocker__email', 'blocker__username',
                     'blocked__email', 'blocked__username']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'created_at'

    def blocker_email(self, obj):
        return obj.blocker.email or obj.blocker.username
    blocker_email.short_description = 'Bllokuesi'
    blocker_email.admin_order_field = 'blocker__email'

    def blocked_email(self, obj):
        return obj.blocked.email or obj.blocked.username
    blocked_email.short_description = 'I bllokuari'
    blocked_email.admin_order_field = 'blocked__email'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('blocker', 'blocked')


@admin.register(OAuthToken)
class OAuthTokenAdmin(admin.ModelAdmin):
    list_display = ['user_identifier', 'provider', 'is_expired', 'created_at']
    list_filter = ['provider']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['id', 'created_at', 'updated_at']

    def user_identifier(self, obj):
        return obj.user.email or obj.user.username
    user_identifier.short_description = 'Përdoruesi'

    def is_expired(self, obj):
        if not obj.expires_at:
            return format_html('<span style="color: gray;">—</span>')
        if obj.expires_at < timezone.now():
            return format_html('<span style="color: red;">✗ Skaduar</span>')
        return format_html('<span style="color: green;">✔ Aktiv</span>')
    is_expired.short_description = 'Statusi'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')