from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from .models import Inquiry, Review
from .serializers import (
    InquiryCreateSerializer, InquiryDetailSerializer,
    ReviewCreateSerializer, ReviewDetailSerializer
)


class InquiryViewSet(viewsets.ModelViewSet):
    serializer_class = InquiryDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'is_reviewed']
    ordering_fields = ['created_at']

    def get_queryset(self):
        user = self.request.user
        # Users see inquiries they made or received
        return Inquiry.objects.filter(
            models.Q(buyer=user) | models.Q(seller=user)
        )

    def get_serializer_class(self):
        if self.action == 'create':
            return InquiryCreateSerializer
        return InquiryDetailSerializer

    def create(self, request, *args, **kwargs):
        """Create inquiry/contact seller"""
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def mark_contacted(self, request, pk=None):
        """Mark inquiry as contacted (only seller can do this)"""
        inquiry = self.get_object()

        if inquiry.seller != request.user:
            return Response(
                {'detail': 'Only seller can mark as contacted'},
                status=status.HTTP_403_FORBIDDEN
            )

        inquiry.mark_contacted()
        return Response({'detail': 'Inquiry marked as contacted'})

    @action(detail=False, methods=['get'])
    def received(self, request):
        """Get inquiries received (as seller)"""
        inquiries = Inquiry.objects.filter(seller=request.user)
        serializer = self.get_serializer(inquiries, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def sent(self, request):
        """Get inquiries sent (as buyer)"""
        inquiries = Inquiry.objects.filter(buyer=request.user)
        serializer = self.get_serializer(inquiries, many=True)
        return Response(serializer.data)


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.filter(is_approved=True)
    serializer_class = ReviewDetailSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['business', 'rating']
    ordering_fields = ['created_at', 'rating']

    def get_serializer_class(self):
        if self.action == 'create':
            return ReviewCreateSerializer
        return ReviewDetailSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    @method_decorator(ratelimit(key='user', rate='5/1d', method='POST'))
    def create(self, request, *args, **kwargs):
        """Create review (rate limited to 5 per day)"""
        return super().create(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def my_reviews(self, request):
        """Get current user's reviews"""
        reviews = Review.objects.filter(user=request.user)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)