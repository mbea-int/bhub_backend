from rest_framework import serializers
from .models import (
    Group, GroupMember, GroupJoinRequest, GroupPost,
    GroupComment, GroupPostLike, GroupMessage
)
from users.serializers import UserListSerializer


class GroupSerializer(serializers.ModelSerializer):
    created_by = UserListSerializer(read_only=True)
    is_member = serializers.SerializerMethodField()
    member_role = serializers.SerializerMethodField()
    member_status = serializers.SerializerMethodField()
    pending_requests_count = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            'id', 'name', 'slug', 'description', 'icon', 'cover_image',
            'category', 'total_members', 'total_posts', 'is_active',
            'require_approval', 'max_images_per_post', 'max_videos_per_post',
            'message_retention_days', 'created_by', 'created_at',
            'is_member', 'member_role', 'member_status', 'pending_requests_count'
        ]
        read_only_fields = ['id', 'slug', 'total_members', 'total_posts', 'created_at']

    def get_is_member(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return GroupMember.objects.filter(
                group=obj,
                user=request.user,
                status='approved'
            ).exists()
        return False

    def get_member_role(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                member = GroupMember.objects.get(
                    group=obj,
                    user=request.user,
                    status='approved'
                )
                return member.role
            except GroupMember.DoesNotExist:
                return None
        return None

    def get_member_status(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                member = GroupMember.objects.get(group=obj, user=request.user)
                return member.status
            except GroupMember.DoesNotExist:
                return None
        return None

    def get_pending_requests_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                member = GroupMember.objects.get(
                    group=obj,
                    user=request.user,
                    status='approved'
                )
                if member.is_admin():
                    return GroupJoinRequest.objects.filter(
                        group=obj,
                        status='pending'
                    ).count()
            except GroupMember.DoesNotExist:
                pass
        return 0

    def validate_name(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Group name must be at least 3 characters")
        return value


class GroupListSerializer(serializers.ModelSerializer):
    """Minimal group info for lists"""
    is_member = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            'id', 'name', 'slug', 'icon', 'category',
            'total_members', 'total_posts', 'is_member'
        ]

    def get_is_member(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return GroupMember.objects.filter(
                group=obj,
                user=request.user,
                status='approved'
            ).exists()
        return False


class GroupMemberSerializer(serializers.ModelSerializer):
    user = UserListSerializer(read_only=True)
    can_manage = serializers.SerializerMethodField()

    class Meta:
        model = GroupMember
        fields = [
            'id', 'user', 'role', 'status', 'joined_at',
            'approved_at', 'can_manage'
        ]

    def get_can_manage(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        try:
            member = GroupMember.objects.get(
                group=obj.group,
                user=request.user,
                status='approved'
            )
            return member.is_admin()
        except GroupMember.DoesNotExist:
            return False


class GroupJoinRequestSerializer(serializers.ModelSerializer):
    user = UserListSerializer(read_only=True)
    group = GroupListSerializer(read_only=True)
    reviewed_by = UserListSerializer(read_only=True)

    class Meta:
        model = GroupJoinRequest
        fields = [
            'id', 'group', 'user', 'message', 'status',
            'reviewed_by', 'reviewed_at', 'rejection_reason',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'reviewed_by', 'reviewed_at',
            'rejection_reason', 'created_at', 'updated_at'
        ]


class GroupPostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupPost
        fields = ['id', 'group', 'content', 'images', 'videos']  # Shto 'id' në response
        read_only_fields = ['id']  # Bëje read-only

    def to_representation(self, instance):
        """Override për të kthyer full object pas krijimit"""
        # Përdor DetailSerializer për response
        serializer = GroupPostDetailSerializer(instance, context=self.context)
        return serializer.data

    def validate(self, attrs):
        request = self.context['request']
        group = attrs['group']

        # Check if user is approved member
        try:
            member = GroupMember.objects.get(group=group, user=request.user)
            if member.status != 'approved':
                raise serializers.ValidationError("You must be an approved member to post")
            if member.status == 'banned':
                raise serializers.ValidationError("You are banned from this group")
        except GroupMember.DoesNotExist:
            raise serializers.ValidationError("You must be a member to post in this group")

        # Validate image count
        images = attrs.get('images', [])
        if len(images) > group.max_images_per_post:
            raise serializers.ValidationError(
                f"Maximum {group.max_images_per_post} images allowed per post"
            )

        # Validate video count
        videos = attrs.get('videos', [])
        if len(videos) > group.max_videos_per_post:
            raise serializers.ValidationError(
                f"Maximum {group.max_videos_per_post} videos allowed per post"
            )

        return attrs

    def create(self, validated_data):
        request = self.context['request']
        validated_data['content'] = validated_data['content'].strip().capitalize()
        post = GroupPost.objects.create(user=request.user, **validated_data)

        # Update group stats
        post.group.total_posts += 1
        post.group.save()

        return post


class GroupPostDetailSerializer(serializers.ModelSerializer):
    user = UserListSerializer(read_only=True)
    group = GroupListSerializer(read_only=True)
    is_liked = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    can_pin = serializers.SerializerMethodField()

    class Meta:
        model = GroupPost
        fields = [
            'id', 'group', 'user', 'content', 'images', 'videos',
            'total_likes', 'total_comments', 'is_pinned', 'is_approved',
            'is_deleted', 'deleted_at', 'deletion_reason',
            'created_at', 'updated_at', 'is_liked',
            'can_edit', 'can_delete', 'can_pin'
        ]

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return GroupPostLike.objects.filter(
                group_post=obj,
                user=request.user
            ).exists()
        return False

    def get_can_edit(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.user == request.user

    def get_can_delete(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        # Post author can delete
        if obj.user == request.user:
            return True

        # Admin/moderator can delete
        try:
            member = GroupMember.objects.get(
                group=obj.group,
                user=request.user,
                status='approved'
            )
            return member.is_moderator()
        except GroupMember.DoesNotExist:
            return False

    def get_can_pin(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        try:
            member = GroupMember.objects.get(
                group=obj.group,
                user=request.user,
                status='approved'
            )
            return member.is_moderator()
        except GroupMember.DoesNotExist:
            return False


class GroupCommentSerializer(serializers.ModelSerializer):
    user = UserListSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()

    class Meta:
        model = GroupComment
        fields = [
            'id', 'user', 'content', 'parent_comment',
            'is_deleted', 'created_at', 'replies', 'can_delete'
        ]
        read_only_fields = ['id', 'user', 'created_at']

    def get_replies(self, obj):
        if obj.parent_comment is None:
            replies = obj.replies.filter(is_deleted=False)
            return GroupCommentSerializer(replies, many=True, context=self.context).data
        return []

    def get_can_delete(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        if obj.user == request.user:
            return True

        try:
            member = GroupMember.objects.get(
                group=obj.group_post.group,
                user=request.user,
                status='approved'
            )
            return member.is_moderator()
        except GroupMember.DoesNotExist:
            return False


class GroupMessageSerializer(serializers.ModelSerializer):
    sender = UserListSerializer(read_only=True)

    class Meta:
        model = GroupMessage
        fields = [
            'id', 'group', 'sender', 'content', 'images',
            'expires_at', 'is_deleted', 'created_at'
        ]
        read_only_fields = ['id', 'sender', 'expires_at', 'created_at']

    def validate(self, attrs):
        request = self.context['request']
        group = attrs['group']

        # Check membership
        try:
            member = GroupMember.objects.get(group=group, user=request.user)
            if member.status != 'approved':
                raise serializers.ValidationError("You must be an approved member")
        except GroupMember.DoesNotExist:
            raise serializers.ValidationError("You must be a member of this group")

        return attrs