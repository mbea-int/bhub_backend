from django.db.models import Count, Q
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters as drf_filters
from django.utils import timezone
from datetime import timedelta
from reviews.models import Review
from reviews.serializers import ReviewDetailSerializer
from django.db.models import Count, Q
from django.utils.functional import cached_property
from django.core.cache import cache
from .models import Business, Follower, Subscriber, BusinessAnalytics, BusinessCategory
from .serializers import (
    BusinessCreateSerializer, BusinessDetailSerializer,
    BusinessListSerializer, BusinessAnalyticsSerializer, BusinessCategorySerializer
)
from businesses.filters.business_filter import BusinessFilter
from utils.permissions import IsBusinessOwner
from core.services.cloudinary_service import CloudinaryService
import logging

logger = logging.getLogger(__name__)


# class BusinessFilter(filters.FilterSet):
#     """Custom filter për Business model"""
#     category = filters.CharFilter(field_name='category__slug', lookup_expr='exact')
#     city = filters.CharFilter(lookup_expr='icontains')
#     is_verified = filters.BooleanFilter()
#     is_premium = filters.BooleanFilter()
#     is_halal_certified = filters.BooleanFilter()
#
#     class Meta:
#         model = Business
#         fields = ['category', 'city', 'is_verified', 'is_premium', 'is_halal_certified']

class BusinessCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BusinessCategory.objects.filter(is_active=True)
    serializer_class = BusinessCategorySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    @cached_property
    def filters(self):
        params = self.request.query_params
        return {
            "city": params.get("city"),
            "is_verified": params.get("is_verified"),
            "is_premium": params.get("is_premium"),
            "is_halal": params.get("is_halal_certified"),
        }

    def get_queryset(self):
        queryset = super().get_queryset()

        # Ndertojme filtrin dinamike vetem nese duhet
        bf = Q()
        if self.filters["city"]:
            bf &= Q(businesses__city__iexact=self.filters["city"])
        if self.filters["is_verified"] is not None:
            bf &= Q(businesses__is_verified=self.filters["is_verified"].lower() == "true")
        if self.filters["is_premium"] is not None:
            bf &= Q(businesses__is_premium=self.filters["is_premium"].lower() == "true")
        if self.filters["is_halal"] is not None:
            bf &= Q(businesses__is_halal_certified=self.filters["is_halal"].lower() == "true")

        # Annotim super-efikas
        return queryset.annotate(
            total_businesses=Count("businesses", filter=bf, distinct=True)
        )


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
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_class = BusinessFilter  # ← PËRDOR CUSTOM FILTER
    # filterset_fields = ['category', 'city', 'is_verified', 'is_premium', 'is_halal_certified']  # ← HEQ KËTË
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

    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to handle slug or ID"""
        try:
            # Try to get by slug first
            instance = self.get_object()
        except Business.DoesNotExist:
            # If slug fails, try ID
            lookup = self.kwargs.get('slug')
            try:
                import uuid
                uuid_obj = uuid.UUID(lookup)
                instance = Business.objects.get(id=uuid_obj)
            except (ValueError, Business.DoesNotExist):
                return Response(
                    {'detail': 'Business not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

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
                data['logo_public_id'] = logo_result['public_id']  # ← SHTO KËTË
                logger.info(f"Logo uploaded: {logo_result['secure_url']}")
            else:
                data['logo'] = None
                data['logo_public_id'] = None

        # Handle halal certificate upload
        if 'halal_certificate' in data and data['halal_certificate']:
            cert_result = CloudinaryService.upload_halal_certificate(
                data['halal_certificate'],
                data.get('business_name', 'business')
            )
            if cert_result:
                data['halal_certificate'] = cert_result['secure_url']
                data['halal_certificate_public_id'] = cert_result['public_id']  # ← SHTO KËTË

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data.copy()

        # ✅ Handle logo update - FSHI TË VJETRËN
        if 'logo' in data:
            new_logo_value = data.get('logo')

            # Nëse logo është empty/null, fshi nga Cloudinary
            if new_logo_value in [None, '', 'null', 'None']:
                logger.info(f"🗑️ Deleting logo for business: {instance.business_name}")

                # Fshi logon e vjetër nga Cloudinary
                if instance.logo_public_id:
                    deleted = CloudinaryService.delete_image(instance.logo_public_id)
                    logger.info(f"Old logo deleted from Cloudinary: {deleted}")

                # Vendos None në databazë
                data['logo'] = None
                data['logo_public_id'] = None

            # Nëse është foto e re (jo URL ekzistues)
            elif not new_logo_value.startswith('http'):
                logger.info(f"📤 Uploading new logo for: {instance.business_name}")

                # Fshi logon e vjetër nëse ekziston
                if instance.logo_public_id:
                    deleted = CloudinaryService.delete_image(instance.logo_public_id)
                    logger.info(f"Old logo deleted before upload: {deleted}")

                # Upload logon e re
                logo_result = CloudinaryService.upload_business_logo(
                    new_logo_value,
                    instance.business_name
                )

                if logo_result:
                    data['logo'] = logo_result['secure_url']
                    data['logo_public_id'] = logo_result['public_id']
                    logger.info(f"✅ New logo uploaded: {logo_result['secure_url']}")
                else:
                    logger.error("❌ Failed to upload new logo")
                    # Nëse dështon upload, mbaj të vjetrën
                    data.pop('logo', None)
                    data.pop('logo_public_id', None)

            # ✅ E njëjta logjikë për halal certificate
        if 'halal_certificate' in data:
            new_cert_value = data.get('halal_certificate')

            if new_cert_value in [None, '', 'null', 'None']:
                if instance.halal_certificate_public_id:
                    CloudinaryService.delete_image(instance.halal_certificate_public_id)
                data['halal_certificate'] = None
                data['halal_certificate_public_id'] = None

            elif not new_cert_value.startswith('http'):
                if instance.halal_certificate_public_id:
                    CloudinaryService.delete_image(instance.halal_certificate_public_id)

                cert_result = CloudinaryService.upload_halal_certificate(
                    new_cert_value,
                    instance.business_name
                )
                if cert_result:
                    data['halal_certificate'] = cert_result['secure_url']
                    data['halal_certificate_public_id'] = cert_result['public_id']

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
        # serializer = BusinessListSerializer(businesses, many=True)
        serializer = BusinessDetailSerializer(
            businesses,
            many=True,
            context={'request': request}  #Shtojme context për computed fields
        )
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

    # kjo mundeson te shtohet endpoint GET /api/businesses/<slug>/reviews/
    @action(
        detail=True,
        methods=['get'],
        url_path='reviews',
        permission_classes=[permissions.AllowAny]
    )
    def get_reviews(self, request, slug=None):
        """
        Return all approved reviews for this business.
        """
        try:
            business = self.get_object()
        except Business.DoesNotExist:
            return Response(
                {'detail': 'Business not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        reviews = Review.objects.filter(
            business=business,
            is_approved=True
        ).order_by('-created_at')

        serializer = ReviewDetailSerializer(reviews, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

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

    #TODO - Kjo pjesë do funksionojë OK për 100–200 biznese, por me 10,000+ do jetë e ngadaltë.
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