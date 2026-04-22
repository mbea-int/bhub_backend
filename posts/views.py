from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.db.models import Count, Q

from .models import Post, PostLike, SavedPost, ProductCategory
from .serializers import (
    PostCreateSerializer, PostDetailSerializer, PostListSerializer,
    ProductCategorySerializer, ProductCategoryCreateSerializer
)
from utils.permissions import IsBusinessOwnerOfPost


class ProductCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing product categories within a business
    """
    serializer_class = ProductCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['display_order', 'name', 'created_at']
    ordering = ['display_order', 'name']

    def get_queryset(self):
        queryset = ProductCategory.objects.all()

        # Filter by business
        business_id = self.request.query_params.get('business')
        if business_id:
            queryset = queryset.filter(business_id=business_id)

        # Filter only active categories
        if self.request.query_params.get('active_only') == 'true':
            queryset = queryset.filter(is_active=True)

        # Përdor emër tjetër për annotation
        queryset = queryset.annotate(
            active_posts_count=Count('posts', filter=Q(posts__is_available=True))
        )

        return queryset

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProductCategoryCreateSerializer
        return ProductCategorySerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        """Create a new product category"""
        business_id = request.data.get('business_id')

        if not business_id:
            return Response(
                {'detail': 'Business ID is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify ownership
        try:
            business = request.user.businesses.get(id=business_id)
        except:
            return Response(
                {'detail': 'Invalid business or you do not own this business.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(
            data=request.data,
            context={'request': request, 'business_id': business_id}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Update product category - only owner can update"""
        instance = self.get_object()

        # Check ownership
        if instance.business.user != request.user:
            return Response(
                {'detail': 'You do not have permission to edit this category.'},
                status=status.HTTP_403_FORBIDDEN
            )

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete product category - only if no posts"""
        instance = self.get_object()

        # Check ownership
        if instance.business.user != request.user:
            return Response(
                {'detail': 'You do not have permission to delete this category.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if category has posts
        if instance.posts.exists():
            return Response(
                {'detail': 'Cannot delete category with existing posts. Please move or delete posts first.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def posts(self, request, pk=None):
        """Get all posts in this category"""
        category = self.get_object()
        posts = Post.objects.filter(
            product_category=category,
            is_available=True
        ).select_related('business', 'business_category')

        serializer = PostListSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.available()
    serializer_class = PostDetailSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['business_category', 'product_category', 'business', 'is_featured']
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
        """Create new post"""
        if not request.user.businesses.exists():
            return Response(
                {'detail': 'Only business owners can create posts'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        post = serializer.save()

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
        """Get featured posts"""
        posts = Post.objects.available().filter(is_featured=True)
        serializer = PostListSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_posts(self, request):
        """Get current user's business posts"""
        posts = Post.objects.filter(business__user=request.user)

        # Filter by product category if specified
        product_category = request.query_params.get('product_category')
        if product_category:
            posts = posts.filter(product_category_id=product_category)

        serializer = PostListSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)