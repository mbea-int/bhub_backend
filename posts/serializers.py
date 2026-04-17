from rest_framework import serializers
from businesses.models import Business, BusinessCategory
from .models import Post, PostLike, SavedPost, PostDailyLimit, ProductCategory
from businesses.serializers import BusinessListSerializer, BusinessCategorySerializer


class ProductCategorySerializer(serializers.ModelSerializer):
    """Serializer for product categories"""
    posts_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = ProductCategory
        fields = [
            'id', 'name', 'slug', 'description', 'icon',
            'display_order', 'is_active', 'posts_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at', 'posts_count']


class ProductCategoryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating product categories"""

    class Meta:
        model = ProductCategory
        fields = ['name', 'description', 'icon', 'display_order']

    def validate(self, attrs):
        request = self.context.get('request')
        business_id = self.context.get('business_id')

        if not business_id:
            raise serializers.ValidationError('Business ID is required.')

        # Check if user owns this business
        try:
            business = request.user.businesses.get(id=business_id)
        except Business.DoesNotExist:
            raise serializers.ValidationError('Invalid business.')

        # Check for duplicate category name within same business
        name = attrs.get('name', '').strip().title()
        if ProductCategory.objects.filter(
                business=business,
                name__iexact=name
        ).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError(
                {'name': 'Kjo kategori ekziston tashmë për këtë biznes.'}
            )

        attrs['business'] = business
        attrs['name'] = name
        return attrs


class PostCreateSerializer(serializers.ModelSerializer):
    business = serializers.PrimaryKeyRelatedField(
        queryset=Business.objects.all(),
        required=True
    )
    business_category = serializers.PrimaryKeyRelatedField(
        queryset=BusinessCategory.objects.all(),
        required=True
    )
    product_category = serializers.PrimaryKeyRelatedField(
        queryset=ProductCategory.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Post
        fields = [
            'product_name', 'description', 'price',
            'business_category', 'product_category',
            'image_url', 'image_thumbnail',
            'auto_share_instagram', 'auto_share_facebook',
            'business'
        ]

    def validate(self, attrs):
        request = self.context['request']
        business = attrs.get('business')
        product_category = attrs.get('product_category')

        if not business:
            raise serializers.ValidationError('Business is required.')

        # Verify user owns this business
        try:
            business = request.user.businesses.get(id=business.id)
        except Business.DoesNotExist:
            raise serializers.ValidationError('Invalid business ID.')

        attrs['business'] = business

        # Verify product_category belongs to this business
        if product_category and product_category.business != business:
            raise serializers.ValidationError(
                'Product category must belong to your business.'
            )

        # Check daily post limit
        if not business.is_within_post_limit():
            raise serializers.ValidationError(
                f"Daily post limit reached ({business.max_posts_per_day} posts per day)"
            )

        return attrs

    def create(self, validated_data):
        validated_data['product_name'] = validated_data['product_name'].strip().title()
        validated_data['description'] = validated_data['description'].strip().capitalize()

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
    business_category = BusinessCategorySerializer(read_only=True)
    product_category = ProductCategorySerializer(read_only=True)
    is_liked = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    can_inquire = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'business', 'product_name', 'description', 'price',
            'business_category', 'product_category',
            'image_url', 'image_thumbnail', 'is_available',
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
        return obj.business.user != request.user


class PostListSerializer(serializers.ModelSerializer):
    """Minimal post info for lists/feeds"""
    business = BusinessListSerializer(read_only=True)
    business_category = BusinessCategorySerializer(read_only=True)
    product_category = ProductCategorySerializer(read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'business', 'product_name', 'price',
            'business_category', 'product_category',
            'image_url', 'image_thumbnail',
            'total_likes', 'created_at', 'is_featured'
        ]