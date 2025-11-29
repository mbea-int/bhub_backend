from rest_framework import serializers

from businesses.models import Business, BusinessCategory
from .models import Post, PostLike, SavedPost, PostDailyLimit
from businesses.serializers import BusinessListSerializer, BusinessCategorySerializer


class PostCreateSerializer(serializers.ModelSerializer):
    business = serializers.PrimaryKeyRelatedField(
        queryset=Business.objects.all(),
        required=True
    )
    category = serializers.PrimaryKeyRelatedField(
        queryset=BusinessCategory.objects.all(),
        required=True
    )

    class Meta:
        model = Post
        fields = [
            'product_name', 'description', 'price', 'category',
            'image_url', 'auto_share_instagram', 'auto_share_facebook',
            'business'
        ]


    def validate(self, attrs):
        request = self.context['request']
        business = attrs.get('business')

        if not business:
            raise serializers.ValidationError('Business is required.')

        try:
            business = request.user.businesses.get(id=business.id)
        except Business.DoesNotExist:
            raise serializers.ValidationError('Invalid business ID.')

        attrs['business'] = business

        # Check daily post limit
        if not business.is_within_post_limit():
            raise serializers.ValidationError(
                f"Daily post limit reached ({business.max_posts_per_day} posts per day)"
            )

        return attrs

    def create(self, validated_data):
        # validated_data.pop('business_id', None)
        validated_data['product_name'] = validated_data['product_name'].strip().capitalize()
        validated_data['description'] = validated_data['description'].strip().capitalize()

        # business = validated_data.pop('business')
        post = Post.objects.create(**validated_data)

        # Update daily limit counter
        from django.utils import timezone
        from django.db.models import F
        today = timezone.now().date()
        obj, created = PostDailyLimit.objects.get_or_create(
            business=post.business,
            date=today,
            defaults={'posts_count': 1}
        )

        if not created:
            obj.posts_count = F('posts_count') + 1
            obj.save()

        return post


class PostDetailSerializer(serializers.ModelSerializer):
    business = BusinessListSerializer(read_only=True)
    category = BusinessCategorySerializer(read_only=True)
    is_liked = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    can_inquire = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'business', 'product_name', 'description', 'price', 'category',
            'image_url', 'is_available',
            'total_likes', 'total_inquiries', 'total_views', 'is_featured',
            'created_at', 'updated_at', 'is_liked', 'is_saved', 'can_inquire'
        ]

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return PostLike.objects.filter(post=obj, user=request.user).exists()
        return False

    def get_is_saved(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return SavedPost.objects.filter(post=obj, user=request.user).exists()
        return False

    def get_can_inquire(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        # Users cannot inquire their own posts
        return obj.business.user != request.user


class PostListSerializer(serializers.ModelSerializer):
    """Minimal post info for lists/feeds"""
    business = BusinessListSerializer(read_only=True)
    category = BusinessCategorySerializer(read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'business', 'product_name', 'price', 'category',
             'total_likes', 'created_at', 'is_featured'
        ]

