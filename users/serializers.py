from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, BlockedUser
from core.services.cloudinary_service import CloudinaryService
import logging

logger = logging.getLogger(__name__)


class CloudinaryImageField(serializers.Field):
    """Custom field to handle Cloudinary image uploads"""

    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        if not data:
            return None

        # If already a URL, return as is
        if isinstance(data, str) and data.startswith('http'):
            return data

        # Otherwise, upload to Cloudinary
        return data

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    referral_code_used = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['email', 'full_name', 'password', 'password_confirm', 'user_type', 'phone', 'referral_code_used']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        referral_code = validated_data.pop('referral_code_used', None)

        user = User.objects.create_user(
            email=validated_data['email'],
            full_name=validated_data['full_name'],
            password=validated_data['password'],
            user_type=validated_data.get('user_type', 'regular'),
            phone=validated_data.get('phone', None)
        )

        # Handle referral
        if referral_code:
            try:
                referrer = User.objects.get(referral_code=referral_code)
                user.referred_by = referrer
                user.save()
            except User.DoesNotExist:
                pass

        return user


class UserProfileSerializer(serializers.ModelSerializer):
    total_referrals = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'phone', 'bio', 'profile_image',
            'user_type', 'referral_code', 'language', 'profile_visibility',
            'is_email_verified', 'created_at', 'total_referrals'
        ]
        read_only_fields = ['id', 'email', 'user_type', 'referral_code', 'is_email_verified', 'created_at']

    def get_total_referrals(self, obj):
        return obj.referrals.count()


# class UserUpgradeSerializer(serializers.Serializer):
#     """Serializer for upgrading user to business owner"""
#     pass  # No input fields needed, just validates the action
#
#     def validate(self, attrs):
#         user = self.context['request'].user
#
#         if user.user_type == 'business':
#             raise serializers.ValidationError("User is already a business owner")
#
#         if user.user_type == 'guest':
#             raise serializers.ValidationError("Guest users cannot become business owners")
#
#         return attrs
#
#     def save(self):
#         user = self.context['request'].user
#         user.user_type = 'business'
#         user.save()
#         return user

class UserUpdateSerializer(serializers.ModelSerializer):
    profile_image = CloudinaryImageField(required=False, allow_null=True)
    class Meta:
        model = User
        fields = ['full_name', 'phone', 'bio', 'profile_image', 'language', 'profile_visibility']

    def validate_phone(self, value):
        if value and not value.startswith('+'):
            raise serializers.ValidationError("Phone number must include country code")
        return value

class UserListSerializer(serializers.ModelSerializer):
    """Minimal user info for lists"""

    class Meta:
        model = User
        fields = ['id', 'full_name', 'profile_image', 'user_type']


class BlockedUserSerializer(serializers.ModelSerializer):
    blocked_user = UserListSerializer(source='blocked', read_only=True)

    class Meta:
        model = BlockedUser
        fields = ['id', 'blocked', 'blocked_user', 'created_at']
        read_only_fields = ['id', 'created_at']