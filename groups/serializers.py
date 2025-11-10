from rest_framework import serializers
from .models import Group, GroupMember, GroupPost, GroupComment, GroupPostLike
from users.serializers import UserListSerializer


class GroupSerializer(serializers.ModelSerializer):
    created_by = UserListSerializer(read_only=True)
    is_member = serializers.SerializerMethodField()
    member_role = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            'id', 'name', 'slug', 'description', 'icon', 'cover_image',
            'category', 'total_members', 'total_posts', 'is_active',
            'created_by', 'created_at', 'is_member', 'member_role'
        ]
        read_only_fields = ['id', 'slug', 'total_members', 'total_posts', 'created_at']

    def get_is_member(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return GroupMember.objects.filter(group=obj, user=request.user).exists()
        return False

    def get_member_role(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                member = GroupMember.objects.get(group=obj, user=request.user)
                return member.role
            except GroupMember.DoesNotExist:
                return None
        return None


class GroupListSerializer(serializers.ModelSerializer):
    """Minimal group info for lists"""

    class Meta:
        model = Group
        fields = ['id', 'name', 'slug', 'icon', 'category', 'total_members', 'total_posts']


class GroupMemberSerializer(serializers.ModelSerializer):
    user = UserListSerializer(read_only=True)

    class Meta:
        model = GroupMember
        fields = ['id', 'user', 'role', 'joined_at']


class GroupPostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupPost
        fields = ['group', 'content', 'images']

    def validate(self, attrs):
        request = self.context['request']
        group = attrs['group']

        # Check if user is member of the group
        if not GroupMember.objects.filter(group=group, user=request.user).exists():
            raise serializers.ValidationError("You must be a member to post in this group")

        return attrs

    def create(self, validated_data):
        request = self.context['request']

        # Auto-capitalize first letter
        validated_data['content'] = validated_data['content'].strip().capitalize()

        post = GroupPost.objects.create(user=request.user, **validated_data)

        # Update group total posts
        post.group.total_posts += 1
        post.group.save()

        return post


class GroupPostDetailSerializer(serializers.ModelSerializer):
    user = UserListSerializer(read_only=True)
    group = GroupListSerializer(read_only=True)
    is_liked = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = GroupPost
        fields = [
            'id', 'group', 'user', 'content', 'images',
            'total_likes', 'total_comments', 'is_pinned', 'is_approved',
            'created_at', 'updated_at', 'is_liked', 'can_edit'
        ]

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return GroupPostLike.objects.filter(group_post=obj, user=request.user).exists()
        return False

    def get_can_edit(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        # Post author or group admin/moderator can edit
        if obj.user == request.user:
            return True

        try:
            member = GroupMember.objects.get(group=obj.group, user=request.user)
            return member.role in ['admin', 'moderator']
        except GroupMember.DoesNotExist:
            return False


class GroupCommentSerializer(serializers.ModelSerializer):
    user = UserListSerializer(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = GroupComment
        fields = ['id', 'user', 'content', 'parent_comment', 'created_at', 'replies']
        read_only_fields = ['id', 'user', 'created_at']

    def get_replies(self, obj):
        if obj.parent_comment is None:  # Only show replies for top-level comments
            replies = obj.replies.all()
            return GroupCommentSerializer(replies, many=True).data
        return []