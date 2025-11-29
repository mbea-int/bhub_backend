from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from .models import Post, PostLike, SavedPost
from .serializers import PostCreateSerializer, PostDetailSerializer, PostListSerializer
from utils.permissions import IsBusinessOwnerOfPost


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.available()
    serializer_class = PostDetailSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'business', 'is_featured']
    search_fields = ['product_name', 'description']
    ordering_fields = ['created_at', 'price', 'total_likes']

    def get_serializer_class(self):
        if self.action == 'create':
            return PostCreateSerializer
        elif self.action == 'list':
            return PostListSerializer
        return PostDetailSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsBusinessOwnerOfPost()]
        return super().get_permissions()

    @method_decorator(ratelimit(key='user', rate='3/1d', method='POST'))
    def create(self, request, *args, **kwargs):
        """Create new post (rate limited to 3 per day)"""
        if not request.user.businesses.exists():
            return Response(
                {'detail': 'Only business owners can create posts'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        post = serializer.save()

        # Update daily post limit
        from django.utils import timezone
        from django.db.models import F
        today = timezone.now().date()
        from .models import PostDailyLimit
        daily_limit, created = PostDailyLimit.objects.get_or_create(
            business=post.business,
            date=today,
            defaults={'posts_count': 1}
        )

        if not created:
            PostDailyLimit.objects.filter(business=post.business, date=today).update(
                posts_count=F('posts_count') + 1
            )

        # Return Post with full detail (including business)
        detail_serializer = PostDetailSerializer(post, context={'request': request})
        headers = self.get_success_headers(detail_serializer.data)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def retrieve(self, request, *args, **kwargs):
        """Get post detail and increment view count"""
        instance = self.get_object()
        instance.increment_views()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Like a post"""
        post = self.get_object()
        like, created = PostLike.objects.get_or_create(post=post, user=request.user)

        if created:
            post.total_likes += 1
            post.save()
            return Response({'detail': 'Post liked successfully'})
        return Response({'detail': 'Already liked'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def unlike(self, request, pk=None):
        """Unlike a post"""
        post = self.get_object()
        deleted = PostLike.objects.filter(post=post, user=request.user).delete()

        if deleted[0] > 0:
            post.total_likes = max(0, post.total_likes - 1)
            post.save()
            return Response({'detail': 'Post unliked successfully'})
        return Response({'detail': 'Not liked'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def save(self, request, pk=None):
        """Save/bookmark a post"""
        post = self.get_object()
        saved, created = SavedPost.objects.get_or_create(post=post, user=request.user)

        if created:
            return Response({'detail': 'Post saved successfully'})
        return Response({'detail': 'Already saved'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def unsave(self, request, pk=None):
        """Unsave/unbookmark a post"""
        post = self.get_object()
        deleted = SavedPost.objects.filter(post=post, user=request.user).delete()

        if deleted[0] > 0:
            return Response({'detail': 'Post unsaved successfully'})
        return Response({'detail': 'Not saved'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def saved(self, request):
        """Get user's saved posts"""
        saved_posts = SavedPost.objects.filter(user=request.user).select_related('post')
        posts = [sp.post for sp in saved_posts]
        serializer = PostListSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured posts (premium businesses)"""
        posts = Post.objects.available().filter(is_featured=True)
        serializer = PostListSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_posts(self, request):
        """Get current user's business posts"""
        if not hasattr(request.user, 'business'):
            return Response({'detail': 'No business profile found'}, status=status.HTTP_404_NOT_FOUND)

        posts = Post.objects.filter(business=request.user.business)
        serializer = PostListSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)