from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .models import (
    Group, GroupMember, GroupJoinRequest, GroupPost,
    GroupComment, GroupPostLike, GroupMessage
)
from .serializers import (
    GroupSerializer, GroupListSerializer, GroupMemberSerializer,
    GroupJoinRequestSerializer, GroupPostCreateSerializer,
    GroupPostDetailSerializer, GroupCommentSerializer, GroupMessageSerializer
)
from utils.permissions import IsAdminUser


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.active()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'total_members', 'total_posts']
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action == 'list':
            return GroupListSerializer
        return GroupSerializer

    def get_permissions(self):
        if self.action in ['create']:
            return [permissions.IsAuthenticated()]  # çdo përdorues i loguar
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAdminUser()]

        # if self.action in ['create', 'update', 'partial_update', 'destroy']:
        #     # Only platform admins can create/edit groups
        #     return [IsAdminUser()]
        return super().get_permissions()

    def perform_create(self, serializer):
        group = serializer.save(created_by=self.request.user)
        # Creator becomes admin automatically
        GroupMember.objects.create(
            group=group,
            user=self.request.user,
            role='admin',
            status='approved',
            approved_at=timezone.now()
        )
        group.total_members = 1
        group.save()

    @action(detail=True, methods=['post'])
    def join(self, request, slug=None):
        """Request to join a group"""
        group = self.get_object()

        # Check if already member
        existing = GroupMember.objects.filter(
            group=group,
            user=request.user
        ).first()

        if existing:
            if existing.status == 'approved':
                return Response(
                    {'detail': 'Already a member', 'status': 'approved'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif existing.status == 'banned':
                return Response(
                    {'detail': 'You are banned from this group'},
                    status=status.HTTP_403_FORBIDDEN
                )
            elif existing.status == 'pending':
                return Response(
                    {'detail': 'Join request pending approval', 'status': 'pending'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Check if there's a pending join request
        existing_request = GroupJoinRequest.objects.filter(
            group=group,
            user=request.user,
            status='pending'
        ).first()

        if existing_request:
            return Response(
                {'detail': 'Join request already pending', 'status': 'pending'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if group.require_approval:
            join_request = GroupJoinRequest.objects.create(
                group=group,
                user=request.user,
                message=request.data.get('message', '')
            )
            GroupMember.objects.create(
                group=group,
                user=request.user,
                role='member',
                status='pending'
            )
            return Response({
                'detail': 'Join request sent. Waiting for admin approval.',
                'status': 'pending',  # ✅ SHTUAR
                'request_id': str(join_request.id),
            })
        else:
            GroupMember.objects.create(
                group=group,
                user=request.user,
                role='member',
                status='approved',
                approved_at=timezone.now()
            )
            group.total_members += 1
            group.save()
            return Response({
                'detail': 'Successfully joined group',
                'status': 'approved',
            })

    @action(detail=True, methods=['post'])
    def leave(self, request, slug=None):
        """Leave a group"""
        group = self.get_object()

        try:
            member = GroupMember.objects.get(group=group, user=request.user)

            # Prevent last admin from leaving
            if member.role == 'admin':
                admin_count = GroupMember.objects.filter(
                    group=group,
                    role='admin',
                    status='approved'
                ).count()
                if admin_count <= 1:
                    return Response(
                        {'detail': 'Cannot leave: You are the last admin. Assign another admin first.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            member.delete()

            if member.status == 'approved':
                group.total_members = max(0, group.total_members - 1)
                group.save()

            return Response({'detail': 'Successfully left group'})
        except GroupMember.DoesNotExist:
            return Response(
                {'detail': 'Not a member'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def members(self, request, slug=None):
        """Get group members"""
        group = self.get_object()
        members = GroupMember.objects.filter(group=group, status='approved')
        serializer = GroupMemberSerializer(members, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def pending_requests(self, request, slug=None):
        """Get pending join requests (admin only)"""
        group = self.get_object()

        # Check if user is admin
        try:
            member = GroupMember.objects.get(
                group=group,
                user=request.user,
                status='approved'
            )
            if not member.is_admin():
                return Response(
                    {'detail': 'Only admins can view pending requests'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except GroupMember.DoesNotExist:
            return Response(
                {'detail': 'Not a member'},
                status=status.HTTP_403_FORBIDDEN
            )

        requests = GroupJoinRequest.objects.filter(group=group, status='pending')
        serializer = GroupJoinRequestSerializer(requests, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def approve_request(self, request, slug=None):
        """Approve a join request (admin only)"""
        group = self.get_object()
        request_id = request.data.get('request_id')

        # Check admin permission
        try:
            member = GroupMember.objects.get(
                group=group,
                user=request.user,
                status='approved'
            )
            if not member.is_admin():
                return Response(
                    {'detail': 'Only admins can approve requests'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except GroupMember.DoesNotExist:
            return Response(
                {'detail': 'Not a member'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            join_request = GroupJoinRequest.objects.get(
                id=request_id,
                group=group,
                status='pending'
            )

            # Update request
            join_request.status = 'approved'
            join_request.reviewed_by = request.user
            join_request.reviewed_at = timezone.now()
            join_request.save()

            # Update member status
            member_obj = GroupMember.objects.get(
                group=group,
                user=join_request.user
            )
            member_obj.status = 'approved'
            member_obj.approved_at = timezone.now()
            member_obj.save()

            # Update group stats
            group.total_members += 1
            group.save()

            return Response({'detail': 'Request approved'})
        except GroupJoinRequest.DoesNotExist:
            return Response(
                {'detail': 'Request not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def reject_request(self, request, slug=None):
        """Reject a join request (admin only)"""
        group = self.get_object()
        request_id = request.data.get('request_id')
        rejection_reason = request.data.get('reason', '')

        # Check admin permission
        try:
            member = GroupMember.objects.get(
                group=group,
                user=request.user,
                status='approved'
            )
            if not member.is_admin():
                return Response(
                    {'detail': 'Only admins can reject requests'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except GroupMember.DoesNotExist:
            return Response(
                {'detail': 'Not a member'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            join_request = GroupJoinRequest.objects.get(
                id=request_id,
                group=group,
                status='pending'
            )

            join_request.status = 'rejected'
            join_request.reviewed_by = request.user
            join_request.reviewed_at = timezone.now()
            join_request.rejection_reason = rejection_reason
            join_request.save()

            # Delete member record
            GroupMember.objects.filter(
                group=group,
                user=join_request.user,
                status='pending'
            ).delete()

            return Response({'detail': 'Request rejected'})
        except GroupJoinRequest.DoesNotExist:
            return Response(
                {'detail': 'Request not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def ban_member(self, request, slug=None):
        """Ban a member (admin only)"""
        group = self.get_object()
        user_id = request.data.get('user_id')
        reason = request.data.get('reason', '')

        # Check admin permission
        try:
            admin_member = GroupMember.objects.get(
                group=group,
                user=request.user,
                status='approved'
            )
            if not admin_member.is_admin():
                return Response(
                    {'detail': 'Only admins can ban members'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except GroupMember.DoesNotExist:
            return Response(
                {'detail': 'Not a member'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            member = GroupMember.objects.get(group=group, user__id=user_id)

            # Cannot ban another admin
            if member.role == 'admin':
                return Response(
                    {'detail': 'Cannot ban another admin'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            member.status = 'banned'
            member.banned_reason = reason
            member.banned_at = timezone.now()
            member.banned_by = request.user
            member.save()

            # Update group stats
            group.total_members = max(0, group.total_members - 1)
            group.save()

            return Response({'detail': 'Member banned'})
        except GroupMember.DoesNotExist:
            return Response(
                {'detail': 'Member not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def remove_member(self, request, slug=None):
        """Remove a member (admin/moderator)"""
        group = self.get_object()
        user_id = request.data.get('user_id')

        # Check permission
        try:
            admin_member = GroupMember.objects.get(
                group=group,
                user=request.user,
                status='approved'
            )
            if not admin_member.is_moderator():
                return Response(
                    {'detail': 'Only admins/moderators can remove members'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except GroupMember.DoesNotExist:
            return Response(
                {'detail': 'Not a member'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            member = GroupMember.objects.get(group=group, user__id=user_id)

            # Cannot remove admin if not admin yourself
            if member.role == 'admin' and not admin_member.is_admin():
                return Response(
                    {'detail': 'Only admins can remove other admins'},
                    status=status.HTTP_403_FORBIDDEN
                )

            member.delete()

            if member.status == 'approved':
                group.total_members = max(0, group.total_members - 1)
                group.save()

            return Response({'detail': 'Member removed'})
        except GroupMember.DoesNotExist:
            return Response(
                {'detail': 'Member not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def promote_member(self, request, slug=None):
        """Promote member to moderator/admin (admin only)"""
        group = self.get_object()
        user_id = request.data.get('user_id')
        new_role = request.data.get('role')  # 'moderator' or 'admin'

        if new_role not in ['moderator', 'admin']:
            return Response(
                {'detail': 'Invalid role'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check admin permission
        try:
            admin_member = GroupMember.objects.get(
                group=group,
                user=request.user,
                status='approved'
            )
            if not admin_member.is_admin():
                return Response(
                    {'detail': 'Only admins can promote members'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except GroupMember.DoesNotExist:
            return Response(
                {'detail': 'Not a member'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            member = GroupMember.objects.get(
                group=group,
                user__id=user_id,
                status='approved'
            )
            member.role = new_role
            member.save()

            return Response({'detail': f'Member promoted to {new_role}'})
        except GroupMember.DoesNotExist:
            return Response(
                {'detail': 'Member not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def my_groups(self, request):
        """Get groups user is member of"""
        memberships = GroupMember.objects.filter(
            user=request.user,
            status='approved'
        ).select_related('group')
        groups = [m.group for m in memberships]
        serializer = GroupListSerializer(groups, many=True, context={'request': request})
        return Response(serializer.data)


class GroupPostViewSet(viewsets.ModelViewSet):
    queryset = GroupPost.objects.filter(is_approved=True, is_deleted=False)
    serializer_class = GroupPostDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    # filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    # filterset_fields = ['group']
    ordering_fields = ['created_at', 'total_likes']

    def get_serializer_class(self):
        if self.action == 'create':
            return GroupPostCreateSerializer
        return GroupPostDetailSerializer

    def get_queryset(self):
        # Only show posts from groups user is member of
        user_groups = GroupMember.objects.filter(
            user=self.request.user,
            status='approved'
        ).values_list('group', flat=True)
        return GroupPost.objects.filter(
            group__in=user_groups,
            is_approved=True,
            is_deleted=False
        )
        # Filtrimi manual për slug ose ID
        group_param = self.request.query_params.get('group')
        if group_param:
            if group_param.isdigit():
                queryset = queryset.filter(group_id=int(group_param))
            else:
                queryset = queryset.filter(group__slug=group_param)

        return queryset

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)

        group_value = self.request.query_params.get("group")
        if group_value:
            if group_value.isdigit():
                # Filter by group ID
                queryset = queryset.filter(group_id=int(group_value))
            else:
                # Filter by slug
                queryset = queryset.filter(group__slug=group_value)

        return queryset

    def perform_destroy(self, instance):
        # Soft delete
        instance.soft_delete(
            deleted_by=self.request.user,
            reason=self.request.data.get('reason', 'Deleted by user')
        )

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Like a group post"""
        post = self.get_object()
        like, created = GroupPostLike.objects.get_or_create(
            group_post=post,
            user=request.user
        )

        if created:
            post.total_likes += 1
            post.save()
            return Response({'detail': 'Post liked'})
        return Response(
            {'detail': 'Already liked'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'])
    def unlike(self, request, pk=None):
        """Unlike a group post"""
        post = self.get_object()
        deleted = GroupPostLike.objects.filter(
            group_post=post,
            user=request.user
        ).delete()

        if deleted[0] > 0:
            post.total_likes = max(0, post.total_likes - 1)
            post.save()
            return Response({'detail': 'Post unliked'})
        return Response(
            {'detail': 'Not liked'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'])
    def pin(self, request, pk=None):
        """Pin/unpin post (admin/moderator only)"""
        post = self.get_object()

        try:
            member = GroupMember.objects.get(
                group=post.group,
                user=request.user,
                status='approved'
            )
            if not member.is_moderator():
                return Response(
                    {'detail': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except GroupMember.DoesNotExist:
            return Response(
                {'detail': 'Not a member'},
                status=status.HTTP_403_FORBIDDEN
            )

        post.is_pinned = not post.is_pinned
        post.save()

        action = 'pinned' if post.is_pinned else 'unpinned'
        return Response({'detail': f'Post {action}'})

    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """Get post comments"""
        post = self.get_object()
        comments = GroupComment.objects.filter(
            group_post=post,
            parent_comment=None,
            is_deleted=False
        )
        serializer = GroupCommentSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        """Add comment to post"""
        post = self.get_object()
        serializer = GroupCommentSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            serializer.save(user=request.user, group_post=post)
            post.total_comments += 1
            post.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)