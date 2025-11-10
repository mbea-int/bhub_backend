from rest_framework import serializers
from .models import Business, Follower, Subscriber, BusinessAnalytics, BusinessCategory
from users.serializers import UserListSerializer


class BusinessCategorySerializer(serializers.ModelSerializer):
    total_businesses = serializers.IntegerField(read_only=True)

    class Meta:
        model = BusinessCategory
        fields = ['id', 'name', 'slug', 'icon', 'description', 'total_businesses']


class BusinessCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = [
            'business_name', 'description', 'category', 'logo',
            'phone', 'email', 'address', 'city', 'country',
            'latitude', 'longitude', 'business_hours',
            'is_halal_certified', 'halal_certificate',
            'social_instagram', 'social_facebook', 'is_primary'
        ]

    def create(self, validated_data):
        user = self.context['request'].user
        if user.user_type != 'business':
            raise serializers.ValidationError("Only business owners can create a business profile")

        # if hasattr(user, 'business'):
        #     raise serializers.ValidationError("User already has a business profile")

        validated_data['user'] = user
        return super().create(validated_data)


class BusinessDetailSerializer(serializers.ModelSerializer):
    owner = UserListSerializer(source='user', read_only=True)
    category = BusinessCategorySerializer(read_only=True)
    is_following = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    distance_km = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Business
        fields = [
            'id', 'owner', 'business_name', 'slug', 'description', 'category',
            'logo', 'phone', 'email', 'address', 'city', 'country',
            'latitude', 'longitude', 'business_hours', 'is_open_now',
            'is_verified', 'verification_status', 'is_premium', 'is_primary',
            'total_followers', 'total_subscribers', 'average_rating', 'total_reviews',
            'is_halal_certified', 'social_instagram', 'social_facebook',
            'created_at', 'is_following', 'is_subscribed', 'distance_km', 'is_mine'
        ]
        read_only_fields = [
            'id', 'slug', 'is_verified', 'verification_status', 'is_premium',
            'total_followers', 'total_subscribers', 'average_rating', 'total_reviews', 'created_at'
        ]

    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Follower.objects.filter(business=obj, user=request.user).exists()
        return False

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscriber.objects.filter(business=obj, user=request.user).exists()
        return False

    def get_distance_km(self, obj):
        # TODO: Calculate distance from user's location
        return None

    def get_is_mine(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.user == request.user
        return False


class BusinessListSerializer(serializers.ModelSerializer):
    """Minimal business info for lists"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)

    class Meta:
        model = Business
        fields = [
            'id', 'business_name', 'slug', 'logo', 'category', 'category_name',
            'category_slug', 'city', 'average_rating', 'total_reviews',
            'is_verified', 'is_premium', 'is_primary', 'is_open_now'
        ]


class BusinessAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessAnalytics
        fields = [
            'date', 'profile_views', 'post_views', 'total_clicks',
            'total_inquiries', 'total_followers_gained'
        ]