from django.db.models import Count
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import timedelta
from .models import Business, Follower, Subscriber, BusinessAnalytics, BusinessCategory
from .serializers import (
    BusinessCreateSerializer, BusinessDetailSerializer,
    BusinessListSerializer, BusinessAnalyticsSerializer, BusinessCategorySerializer
)
from utils.permissions import IsBusinessOwner
from core.services.cloudinary_service import CloudinaryService
import logging

logger = logging.getLogger(__name__)


class BusinessCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BusinessCategory.objects.filter(is_active=True)
    serializer_class = BusinessCategorySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.annotate(
            total_businesses=Count('businesses')
        )
        return queryset

    @action(detail=False, methods=['get'])
    def debug(self, request):
        """Debug endpoint to check categories"""
        categories = self.get_queryset()
        return Response({
            'count': categories.count(),
            'categories': BusinessCategorySerializer(categories, many=True).data
        })

class BusinessViewSet(viewsets.ModelViewSet):
    queryset = Business.objects.active()
    serializer_class = BusinessDetailSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'city', 'is_verified', 'is_premium', 'is_halal_certified']
    search_fields = ['business_name', 'description', 'address']
    ordering_fields = ['created_at', 'average_rating', 'total_followers']
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action == 'create':
            return BusinessCreateSerializer
        elif self.action == 'list':
            return BusinessListSerializer
        return BusinessDetailSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsBusinessOwner()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        data = request.data.copy()

        # Handle logo upload
        if 'logo' in data and data['logo']:
            logo_result = CloudinaryService.upload_business_logo(
                data['logo'],
                data.get('business_name', 'business')
            )
            if logo_result:
                data['logo'] = logo_result['secure_url']
                logger.info(f"Logo uploaded successfully: {logo_result['secure_url']}")
            else:
                logger.error("Failed to upload logo to Cloudinary")
                data['logo'] = None

        # Handle halal certificate upload
        if 'halal_certificate' in data and data['halal_certificate']:
            cert_result = CloudinaryService.upload_halal_certificate(
                data['halal_certificate'],
                data.get('business_name', 'business')
            )
            if cert_result:
                data['halal_certificate'] = cert_result['secure_url']
                logger.info(f"Certificate uploaded successfully: {cert_result['secure_url']}")
            else:
                logger.error("Failed to upload certificate to Cloudinary")
                data['halal_certificate'] = None

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data.copy()

        # Handle logo update
        if 'logo' in data and data['logo'] and not data['logo'].startswith('http'):
            # Delete old logo if exists
            if instance.logo:
                old_public_id = instance.logo.split('/')[-1].split('.')[0]
                CloudinaryService.delete_image(old_public_id)

            # Upload new logo
            logo_result = CloudinaryService.upload_business_logo(
                data['logo'],
                instance.business_name
            )
            if logo_result:
                data['logo'] = logo_result['secure_url']

        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_business(self, request):
        """Get current user's business"""
        try:
            business = request.user.primary_business
            serializer = self.get_serializer(business)
            return Response(serializer.data)
        except Business.DoesNotExist:
            return Response({'detail': 'No business profile found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def my_businesses(self, request):
        """Get all businesses owned by current user"""
        businesses = request.user.businesses.all()
        serializer = BusinessListSerializer(businesses, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsBusinessOwner])
    def set_primary(self, request, slug=None):
        """Set a business as primary"""
        business = self.get_object()

        # Remove primary from other businesses
        request.user.businesses.update(is_primary=False)

        # Set this as primary
        business.is_primary = True
        business.save()

        return Response({'detail': 'Business set as primary'})

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def switch_context(self, request):
        """Switch active business context"""
        business_id = request.data.get('business_id')

        try:
            business = request.user.businesses.get(id=business_id)
            # You can store this in session or return it as needed
            return Response({
                'active_business': BusinessDetailSerializer(business).data
            })
        except Business.DoesNotExist:
            return Response(
                {'detail': 'Business not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def follow(self, request, slug=None):
        """Follow a business"""
        business = self.get_object()
        follower, created = Follower.objects.get_or_create(
            business=business,
            user=request.user
        )

        if created:
            business.total_followers += 1
            business.save()
            return Response({'detail': 'Successfully followed business'})
        return Response({'detail': 'Already following this business'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def unfollow(self, request, slug=None):
        """Unfollow a business"""
        business = self.get_object()
        deleted = Follower.objects.filter(business=business, user=request.user).delete()

        if deleted[0] > 0:
            business.total_followers = max(0, business.total_followers - 1)
            business.save()
            return Response({'detail': 'Successfully unfollowed business'})
        return Response({'detail': 'Not following this business'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def subscribe(self, request, slug=None):
        """Subscribe to business notifications"""
        business = self.get_object()
        subscriber, created = Subscriber.objects.get_or_create(
            business=business,
            user=request.user
        )

        if created:
            business.total_subscribers += 1
            business.save()
            return Response({'detail': 'Successfully subscribed to notifications'})
        return Response({'detail': 'Already subscribed'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def unsubscribe(self, request, slug=None):
        """Unsubscribe from business notifications"""
        business = self.get_object()
        deleted = Subscriber.objects.filter(business=business, user=request.user).delete()

        if deleted[0] > 0:
            business.total_subscribers = max(0, business.total_subscribers - 1)
            business.save()
            return Response({'detail': 'Successfully unsubscribed'})
        return Response({'detail': 'Not subscribed'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], permission_classes=[IsBusinessOwner])
    def analytics(self, request, slug=None):
        """Get business analytics (last 30 days)"""
        business = self.get_object()
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)

        analytics = BusinessAnalytics.objects.filter(
            business=business,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('-date')

        serializer = BusinessAnalyticsSerializer(analytics, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def premium(self, request):
        """Get premium businesses"""
        businesses = Business.objects.premium()
        serializer = BusinessListSerializer(businesses, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """Get nearby businesses (requires lat/lng params)"""
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius_km = request.query_params.get('radius', 10)  # Default 10km

        if not lat or not lng:
            return Response(
                {'detail': 'Latitude and longitude are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from django.contrib.gis.measure import Distance
            from django.contrib.gis.geos import Point
            from django.db.models import F
            from math import radians, cos, sin, asin, sqrt

            # Haversine formula for distance calculation
            # (Simplified version without PostGIS)
            businesses = Business.objects.active().filter(
                latitude__isnull=False,
                longitude__isnull=False
            )

            # Filter by rough bounding box first (performance optimization)
            lat_float = float(lat)
            lng_float = float(lng)

            nearby = []
            for business in businesses:
                # Calculate distance using Haversine formula
                lat1, lng1 = radians(lat_float), radians(lng_float)
                lat2, lng2 = radians(float(business.latitude)), radians(float(business.longitude))

                dlat = lat2 - lat1
                dlng = lng2 - lng1

                a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
                c = 2 * asin(sqrt(a))
                distance = 6371 * c  # Radius of Earth in km

                if distance <= float(radius_km):
                    nearby.append((business, distance))

            # Sort by distance
            nearby.sort(key=lambda x: x[1])
            businesses_sorted = [b[0] for b in nearby]

            serializer = BusinessListSerializer(businesses_sorted, many=True)
            return Response(serializer.data)

        except Exception as e:
            return Response(
                {'detail': f'Error calculating distance: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )