from django.contrib import admin
from django.utils.html import format_html
from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['reporter', 'reported_type', 'reason', 'status', 'created_at', 'action_links']
    list_filter = ['reported_type', 'reason', 'status', 'created_at']
    search_fields = ['reporter__email', 'description', 'admin_note']
    ordering = ['-created_at']
    readonly_fields = ['reporter', 'created_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Report Info', {
            'fields': ('reporter', 'reported_type', 'reported_id', 'reason', 'description')
        }),
        ('Status', {
            'fields': ('status', 'admin_note', 'resolved_by', 'resolved_at')
        }),
        ('Dates', {
            'fields': ('created_at',)
        }),
    )

    actions = ['mark_reviewing', 'mark_resolved', 'mark_dismissed']

    def action_links(self, obj):
        return format_html(
            '<a class="button" href="{}">View Reported Item</a>',
            f'/admin/{obj.reported_type}/{obj.reported_id}/'
        )

    action_links.short_description = 'Actions'

    def mark_reviewing(self, request, queryset):
        queryset.update(status='reviewing')
        self.message_user(request, f'{queryset.count()} reports marked as reviewing')

    mark_reviewing.short_description = 'Mark as under review'

    def mark_resolved(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='resolved', resolved_by=request.user, resolved_at=timezone.now())
        self.message_user(request, f'{queryset.count()} reports resolved')

    mark_resolved.short_description = 'Mark as resolved'

    def mark_dismissed(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='dismissed', resolved_by=request.user, resolved_at=timezone.now())
        self.message_user(request, f'{queryset.count()} reports dismissed')

    mark_dismissed.short_description = 'Dismiss reports'