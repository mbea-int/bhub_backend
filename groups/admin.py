from django.contrib import admin
from .models import Group, GroupMember, GroupPost, GroupComment

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'total_members', 'total_posts', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['total_members', 'total_posts', 'created_at', 'updated_at']
    # prepopulated_fields = {'slug': ('name',)}

@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ['group', 'user', 'role', 'joined_at']
    list_filter = ['role', 'joined_at']
    search_fields = ['group__name', 'user__email']
    date_hierarchy = 'joined_at'

@admin.register(GroupPost)
class GroupPostAdmin(admin.ModelAdmin):
    list_display = ['group', 'user', 'is_pinned', 'is_approved', 'total_likes', 'total_comments', 'created_at']
    list_filter = ['is_pinned', 'is_approved', 'created_at']
    search_fields = ['content', 'group__name', 'user__email']
    date_hierarchy = 'created_at'

@admin.register(GroupComment)
class GroupCommentAdmin(admin.ModelAdmin):
    list_display = ['group_post', 'user', 'parent_comment', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content', 'user__email']
    date_hierarchy = 'created_at'