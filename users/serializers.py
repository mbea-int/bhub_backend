from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, BlockedUser
from core.services.cloudinary_service import CloudinaryService
import logging

logger = logging.getLogger(__name__)


class CloudinaryImageField(serializers.Field):
    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        if not data:
            return None
        if isinstance(data, str) and data.startswith('http'):
            return data
        return data


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)
    referral_code_used = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )
    # Username opsional — mund të përdoret për login
    username = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        min_length=3,
        max_length=50
    )
    # Email opsional për regular, i rekomanduar për biznes
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = User
        fields = [
            'email', 'username', 'full_name', 'password', 'password_confirm',
            'user_type', 'phone', 'referral_code_used'
        ]

    def validate_username(self, value):
        if not value:
            return None
        value = value.strip().lower()
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('Ky username është i zënë.')
        # Lejo vetëm shkronja, numra, nënvija
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError(
                'Username mund të ketë vetëm shkronja, numra dhe nënvija (_).'
            )
        return value

    def validate_email(self, value):
        if not value:
            return None
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Ky email është i regjistruar tashmë.')
        return value

    def validate(self, attrs):
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        user_type = attrs.get('user_type', 'regular')
        email = attrs.get('email')
        username = attrs.get('username')
        phone = attrs.get('phone')

        # Fjalëkalimet
        if password != password_confirm:
            raise serializers.ValidationError(
                {'password': 'Fjalëkalimet nuk përputhen.'}
            )

        # Rregull 1: Çdo user duhet email OSE username
        if not email and not username:
            raise serializers.ValidationError(
                {'email': 'Duhet të vendosni email ose username.'}
            )

        # Rregull 2: Bizneset duhet email OSE phone
        if user_type == 'business' and not email and not phone:
            raise serializers.ValidationError(
                {'phone': 'Bizneset duhet të kenë email ose numër telefoni.'}
            )

        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        referral_code = validated_data.pop('referral_code_used', None)
        password = validated_data.pop('password')

        # Pastro fushat boshe
        email = validated_data.get('email') or None
        username = validated_data.get('username') or None

        user = User.objects.create_user(
            email=email,
            full_name=validated_data['full_name'],
            password=password,
            user_type=validated_data.get('user_type', 'regular'),
            phone=validated_data.get('phone') or None,
            username=username,
        )

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
    total_posts = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    total_saved = serializers.SerializerMethodField()
    can_make_inquiry = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'full_name', 'phone', 'bio',
            'profile_image', 'user_type', 'referral_code', 'language',
            'profile_visibility', 'is_email_verified', 'created_at',
            'total_referrals', 'total_posts', 'average_rating',
            'total_saved', 'can_make_inquiry'
        ]
        read_only_fields = [
            'id', 'user_type', 'referral_code',
            'is_email_verified', 'created_at'
        ]

    def get_total_referrals(self, obj):
        return obj.referrals.count()

    def get_total_posts(self, obj):
        from posts.models import Post
        if obj.user_type == 'business':
            business_ids = obj.businesses.values_list('id', flat=True)
            return Post.objects.filter(business_id__in=business_ids).count()
        return 0

    def get_average_rating(self, obj):
        from django.db.models import Avg
        if obj.user_type == 'business':
            result = obj.businesses.aggregate(avg=Avg('average_rating'))
            avg = result['avg']
            return float(avg) if avg else 0.0
        return 0.0

    def get_total_saved(self, obj):
        from posts.models import SavedPost
        return SavedPost.objects.filter(user=obj).count()


class UserUpdateSerializer(serializers.ModelSerializer):
    profile_image = CloudinaryImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            'full_name', 'username', 'phone', 'bio',
            'profile_image', 'language', 'profile_visibility'
        ]

    def validate_username(self, value):
        if not value:
            return None

        value = value.strip().lower()
        user = self.instance

        # Kontrollo nëse po ndryshon (jo vetëm konfirmon të njëjtin)
        if user and user.username and user.username == value:
            return value  # S'ka ndryshim, kalon pa problem

        # Kontrollo kufizimin 30-ditor
        if user and user.username_changed_at:
            from django.utils import timezone
            days_since = (timezone.now() - user.username_changed_at).days
            if days_since < 30:
                remaining = 30 - days_since
                raise serializers.ValidationError(
                    f'Username mund të ndryshohet pas {remaining} ditësh.'
                )

        # Kontrollo unikalitetin
        if User.objects.filter(username__iexact=value).exclude(
            pk=user.pk if user else None
        ).exists():
            raise serializers.ValidationError('Ky username është i zënë.')

        # Kontrollo formatin
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError(
                'Username mund të ketë vetëm shkronja, numra dhe nënvija (_).'
            )

        if len(value) < 3:
            raise serializers.ValidationError(
                'Username duhet të ketë të paktën 3 karaktere.'
            )

        return value

    def validate_phone(self, value):
        if value and not value.startswith('+'):
            raise serializers.ValidationError(
                'Numri duhet të përfshijë kodin e vendit (+355...)'
            )
        return value

    def update(self, instance, validated_data):
        # Nëse username po ndryshon, ruaj timestamp-in
        new_username = validated_data.get('username')
        if new_username and new_username != instance.username:
            from django.utils import timezone
            validated_data['username_changed_at'] = timezone.now()

        return super().update(instance, validated_data)


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'full_name', 'username', 'profile_image', 'user_type']


class BlockedUserSerializer(serializers.ModelSerializer):
    blocked_user = UserListSerializer(source='blocked', read_only=True)

    class Meta:
        model = BlockedUser
        fields = ['id', 'blocked', 'blocked_user', 'created_at']
        read_only_fields = ['id', 'created_at']