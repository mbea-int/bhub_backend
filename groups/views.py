from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Group, GroupMember, GroupPost, GroupComment, GroupPostLike
from .serializers import (
    GroupSerializer, GroupListSerializer, GroupMemberSerializer,
    GroupPostCreateSerializer, GroupPostDetailSerializer, GroupCommentSerializer
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
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]  # Only admins can create/edit groups
        return super().get_permissions()

    @action(detail=True, methods=['post'])
    def join(self, request, slug=None):
        """Join a group"""
        group = self.get_object()
        member, created = GroupMember.objects.get_or_create(
            group=group,
            user=request.user,
            defaults={'role': 'member'}
        )

        if created:
            group.total_members += 1
            group.save()
            return Response({'detail': 'Successfully joined group'})
        return Response({'detail': 'Already a member'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def leave(self, request, slug=None):
        """Leave a group"""
        group = self.get_object()
        deleted = GroupMember.objects.filter(group=group, user=request.user).delete()

        if deleted[0] > 0:
            group.total_members = max(0, group.total_members - 1)
            group.save()
            return Response({'detail': 'Successfully left group'})
        return Response({'detail': 'Not a member'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def members(self, request, slug=None):
        """Get group members"""
        group = self.get_object()
        members = GroupMember.objects.filter(group=group)
        serializer = GroupMemberSerializer(members, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_groups(self, request):
        """Get groups user is member of"""
        memberships = GroupMember.objects.filter(user=request.user)
        groups = [m.group for m in memberships]
        serializer = GroupListSerializer(groups, many=True)
        return Response(serializer.data)


class GroupPostViewSet(viewsets.ModelViewSet):
    queryset = GroupPost.objects.filter(is_approved=True)
    serializer_class = GroupPostDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['group']
    ordering_fields = ['created_at', 'total_likes']

    def get_serializer_class(self):
        if self.action == 'create':
            return GroupPostCreateSerializer
        return GroupPostDetailSerializer

    def get_queryset(self):
        # Only show posts from groups user is member of
        user_groups = GroupMember.objects.filter(user=self.request.user).values_list('group', flat=True)
        return GroupPost.objects.filter(group__in=user_groups, is_approved=True)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Like a group post"""
        post = self.get_object()
        like, created = GroupPostLike.objects.get_or_create(group_post=post, user=request.user)

        if created:
            post.total_likes += 1
            post.save()
            return Response({'detail': 'Post liked'})
        return Response({'detail': 'Already liked'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def unlike(self, request, pk=None):
        """Unlike a group post"""
        post = self.get_object()
        deleted = GroupPostLike.objects.filter(group_post=post, user=request.user).delete()

        if deleted[0] > 0:
            post.total_likes = max(0, post.total_likes - 1)
            post.save()
            return Response({'detail': 'Post unliked'})
        return Response({'detail': 'Not liked'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def pin(self, request, pk=None):
        """Pin post (admin/moderator only)"""
        post = self.get_object()

        # Check if user is admin/moderator
        try:
            member = GroupMember.objects.get(group=post.group, user=request.user)
            if member.role not in ['admin', 'moderator']:
                return Response({'detail': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        except GroupMember.DoesNotExist:
            return Response({'detail': 'Not a member'}, status=status.HTTP_403_FORBIDDEN)

        post.is_pinned = True
        post.save()
        return Response({'detail': 'Post pinned'})

    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """Get post comments"""
        post = self.get_object()
        comments = GroupComment.objects.filter(group_post=post, parent_comment=None)
        serializer = GroupCommentSerializer(comments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        """Add comment to post"""
        post = self.get_object()
        serializer = GroupCommentSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=request.user, group_post=post)
            post.total_comments += 1
            post.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)