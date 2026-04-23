# users/serializers.py

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, BlockedUser
from core.services.cloudinary_service import CloudinaryService
import logging
import re

logger = logging.getLogger(__name__)


def normalize_phone(value):
    """
    Normalizon numrin e telefonit:
    - 068... → +355 68...
    - 06x... → +355 6x...
    - +355... → mbetet
    - Heq hapësirat, vizat
    """
    if not value:
        return None

    # Pastro hapësirat dhe vizat
    cleaned = re.sub(r'[\s\-\(\)]+', '', value.strip())

    if not cleaned:
        return None

    # Nëse fillon me 0 (format shqiptar lokal)
    if cleaned.startswith('0') and not cleaned.startswith('00'):
        cleaned = '+355' + cleaned[1:]

    # Nëse fillon me 00355
    if cleaned.startswith('00355'):
        cleaned = '+355' + cleaned[5:]

    # Nëse nuk ka prefix, supozo shqiptar
    if not cleaned.startswith('+'):
        # Nëse duket si numër shqiptar (fillon me 6)
        if cleaned.startswith('6') and len(cleaned) >= 8:
            cleaned = '+355' + cleaned
        else:
            cleaned = '+' + cleaned

    return cleaned


def validate_phone_number(value):
    """Validon numrin e telefonit pas normalizimit"""
    if not value:
        return

    normalized = normalize_phone(value)
    if not normalized:
        return

    # Kontrollo formatin bazë: + pastaj numra, min 10 karaktere
    if not re.match(r'^\+\d{10,15}$', normalized):
        raise serializers.ValidationError(
            'Numri i telefonit nuk është i vlefshëm. '
            'Mund të shkruani 068..., +355 68..., ose formatin ndërkombëtar.'
        )


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
    username = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        min_length=3,
        max_length=50
    )
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

    def validate_phone(self, value):
        if not value or not value.strip():
            return None
        normalized = normalize_phone(value)
        validate_phone_number(value)
        return normalized

    def validate(self, attrs):
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        user_type = attrs.get('user_type', 'regular')
        email = attrs.get('email')
        username = attrs.get('username')
        phone = attrs.get('phone')

        if password != password_confirm:
            raise serializers.ValidationError(
                {'password': 'Fjalëkalimet nuk përputhen.'}
            )

        if not email and not username:
            raise serializers.ValidationError(
                {'email': 'Duhet të vendosni email ose username.'}
            )

        if user_type == 'business' and not email and not phone:
            raise serializers.ValidationError(
                {'phone': 'Bizneset duhet të kenë email ose numër telefoni.'}
            )

        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        referral_code = validated_data.pop('referral_code_used', None)
        password = validated_data.pop('password')

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
            'profile_visibility', 'is_email_verified', 'is_phone_verified',
            'created_at', 'total_referrals', 'total_posts', 'average_rating',
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
    email = serializers.EmailField(required=False, allow_null=True, allow_blank=True)
    phone = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'full_name', 'username', 'email', 'phone', 'bio',
            'profile_image', 'language', 'profile_visibility'
        ]

    def validate_email(self, value):
        # ✅ String bosh = fshi email-in
        if value is None or (isinstance(value, str) and not value.strip()):
            return ''  # Kthe string bosh (do ta trajtojmë në update)

        value = value.strip().lower()
        user = self.instance

        if user and user.email and user.email.lower() == value:
            return value

        if User.objects.filter(email__iexact=value).exclude(
            pk=user.pk if user else None
        ).exists():
            raise serializers.ValidationError('Ky email është i regjistruar tashmë.')

        return value

    def validate_username(self, value):
        if not value:
            return None

        value = value.strip().lower()
        user = self.instance

        if user and user.username and user.username == value:
            return value

        if user and user.username_changed_at:
            from django.utils import timezone
            days_since = (timezone.now() - user.username_changed_at).days
            if days_since < 30:
                remaining = 30 - days_since
                raise serializers.ValidationError(
                    f'Username mund të ndryshohet pas {remaining} ditësh.'
                )

        if User.objects.filter(username__iexact=value).exclude(
            pk=user.pk if user else None
        ).exists():
            raise serializers.ValidationError('Ky username është i zënë.')

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
        # ✅ String bosh = fshi phone
        if value is None or (isinstance(value, str) and not value.strip()):
            return ''  # Kthe string bosh (do ta trajtojmë në update)

        normalized = normalize_phone(value)
        validate_phone_number(value)
        return normalized

    def validate(self, attrs):
        """
        Validim i përgjithshëm:
        - Business users duhet të kenë të paktën email OSE phone
        """
        user = self.instance
        if user and user.user_type == 'business':
            # Merr vlerat finale (pas update)
            final_email = attrs.get('email', user.email)
            final_phone = attrs.get('phone', user.phone)

            # String bosh = fshirje
            if final_email == '':
                final_email = None
            if final_phone == '':
                final_phone = None

            if not final_email and not final_phone:
                raise serializers.ValidationError({
                    'email': 'Bizneset duhet të kenë të paktën email ose numër telefoni.',
                    'phone': 'Bizneset duhet të kenë të paktën email ose numër telefoni.',
                })

        return attrs

    def update(self, instance, validated_data):
        # ─── Username change tracking ───
        new_username = validated_data.get('username')
        if new_username and new_username != instance.username:
            from django.utils import timezone
            validated_data['username_changed_at'] = timezone.now()

        # ─── Email change handling ───
        if 'email' in validated_data:
            new_email = validated_data['email']

            if new_email == '':
                # ✅ FSHI email-in
                validated_data['email'] = None
                validated_data['is_email_verified'] = False
                validated_data['email_verification_code'] = None
                validated_data['email_verification_code_sent_at'] = None
                logger.info(f"Email removed for user {instance.id}")

            elif new_email and new_email != instance.email:
                # Email ndryshoi - flag-o si jo-verified
                validated_data['is_email_verified'] = False
                validated_data['email_verification_code'] = None
                validated_data['email_verification_code_sent_at'] = None
                logger.info(
                    f"Email changed for user {instance.id}: "
                    f"{instance.email} → {new_email}"
                )

        # ─── Phone change handling ───
        if 'phone' in validated_data:
            new_phone = validated_data['phone']

            if new_phone == '':
                # ✅ FSHI phone
                validated_data['phone'] = None
                validated_data['is_phone_verified'] = False
                logger.info(f"Phone removed for user {instance.id}")

            elif new_phone and new_phone != instance.phone:
                # Phone ndryshoi - flag-o si jo-verified
                validated_data['is_phone_verified'] = False
                logger.info(
                    f"Phone changed for user {instance.id}: "
                    f"{instance.phone} → {new_phone}"
                )

        return super().update(instance, validated_data)


class UpgradeEligibilitySerializer(serializers.Serializer):
    """Serializer për përgjigjen e eligibility check"""
    eligible = serializers.BooleanField()
    has_email = serializers.BooleanField()
    has_phone = serializers.BooleanField()
    requirements_met = serializers.BooleanField()
    missing = serializers.ListField(child=serializers.CharField(), required=False)
    message = serializers.CharField(required=False)


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