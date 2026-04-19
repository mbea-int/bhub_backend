# messaging/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = [
        'short_id', 'sender_email', 'receiver_email',
        'short_content', 'is_read', 'has_attachment',
        'is_deleted', 'created_at'
    ]
    list_filter = [
        'is_read', 'is_deleted', 'attachment_type',
        'created_at',
    ]
    search_fields = [
        'sender__email', 'receiver__email',
        'content', 'conversation_id',
    ]
    readonly_fields = [
        'id', 'conversation_id', 'sender', 'receiver',
        'created_at', 'read_at', 'deleted_at',
        'related_business', 'related_post',
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    fieldsets = (
        ('Identifikimi', {
            'fields': ('id', 'conversation_id')
        }),
        ('Pjesëmarrësit', {
            'fields': ('sender', 'receiver')
        }),
        ('Mesazhi', {
            'fields': ('content', 'attachment', 'attachment_type')
        }),
        ('Statusi', {
            'fields': ('is_read', 'read_at', 'is_deleted', 'deleted_at')
        }),
        ('Lidhjet', {
            'fields': ('related_business', 'related_post'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def short_id(self, obj):
        return str(obj.id)[:8] + '...'
    short_id.short_description = 'ID'

    def sender_email(self, obj):
        return obj.sender.email
    sender_email.short_description = 'Dërguesi'
    sender_email.admin_order_field = 'sender__email'

    def receiver_email(self, obj):
        return obj.receiver.email
    receiver_email.short_description = 'Marrësi'
    receiver_email.admin_order_field = 'receiver__email'

    def short_content(self, obj):
        return obj.content[:60] + '...' if len(obj.content) > 60 else obj.content
    short_content.short_description = 'Përmbajtja'

    def has_attachment(self, obj):
        if obj.attachment:
            return format_html('<span style="color: green;">✔ {}</span>', obj.attachment_type)
        return format_html('<span style="color: #ccc;">—</span>')
    has_attachment.short_description = 'Bashkëngjitje'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'sender', 'receiver', 'related_business', 'related_post'
        )