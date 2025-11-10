from rest_framework import serializers
from .models import Inquiry, Review
from users.serializers import UserListSerializer
from posts.serializers import PostListSerializer


class InquiryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inquiry
        fields = ['post', 'buyer_name', 'buyer_phone', 'buyer_address', 'message']

    def validate(self, attrs):
        request = self.context['request']
        post = attrs['post']

        # Cannot inquire own post
        if post.business.user == request.user:
            raise serializers.ValidationError("Cannot inquire your own post")

        return attrs

    def create(self, validated_data):
        request = self.context['request']
        post = validated_data['post']

        inquiry = Inquiry.objects.create(
            buyer=request.user,
            seller=post.business.user,
            **validated_data
        )

        # Increment post inquiries
        post.total_inquiries += 1
        post.save()

        return inquiry


class InquiryDetailSerializer(serializers.ModelSerializer):
    buyer = UserListSerializer(read_only=True)
    seller = UserListSerializer(read_only=True)
    post = PostListSerializer(read_only=True)

    class Meta:
        model = Inquiry
        fields = [
            'id', 'post', 'buyer', 'seller', 'buyer_name', 'buyer_phone',
            'buyer_address', 'message', 'status', 'is_reviewed',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'buyer', 'seller', 'is_reviewed', 'created_at', 'updated_at']


class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['business', 'inquiry', 'rating', 'comment', 'images']

    def validate(self, attrs):
        request = self.context['request']
        business = attrs['business']
        inquiry = attrs.get('inquiry')

        # Check if user has inquiry with this business
        if inquiry:
            if inquiry.buyer != request.user:
                raise serializers.ValidationError("Can only review inquiries you made")
            if inquiry.status not in ['contacted', 'completed']:
                raise serializers.ValidationError("Cannot review until inquiry is contacted/completed")
            if inquiry.is_reviewed:
                raise serializers.ValidationError("Already reviewed this inquiry")

        # Check rating and comment requirement
        if attrs['rating'] <= 3 and not attrs.get('comment'):
            raise serializers.ValidationError("Comment is required for ratings 3 or below")

        # Check if already reviewed
        existing = Review.objects.filter(business=business, user=request.user, inquiry=inquiry).exists()
        if existing:
            raise serializers.ValidationError("Already reviewed this business/inquiry")

        return attrs

    def create(self, validated_data):
        request = self.context['request']
        return Review.objects.create(user=request.user, **validated_data)


class ReviewDetailSerializer(serializers.ModelSerializer):
    user = UserListSerializer(read_only=True)

    class Meta:
        model = Review
        fields = [
            'id', 'user', 'rating', 'comment', 'images',
            'is_approved', 'created_at'
        ]