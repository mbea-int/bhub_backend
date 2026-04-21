import uuid
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
import random
import string


class UserManager(BaseUserManager):
    def active_users(self):
        return self.filter(is_active=True, is_banned=False)

    def create_user(self, email=None, full_name='', password=None, **extra_fields):
        if email:
            email = self.normalize_email(email)
        user = self.model(email=email, full_name=full_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, full_name, password, **extra_fields)

    def create_guest_user(self):
        import secrets
        guest_email = f"guest_{secrets.token_hex(8)}@temp.local"
        guest = self.model(
            email=guest_email,
            full_name="Guest user",
            user_type="guest",
            is_active=True,
            is_guest=True
        )
        guest.set_unusable_password()
        guest.save(using=self._db)
        return guest


class User(AbstractUser):
    USER_TYPE_CHOICES = [
        ('regular', 'Regular User'),
        ('business', 'Business Owner'),
        ('guest', 'Guest'),
    ]

    LANGUAGE_CHOICES = [
        ('sq', 'Albanian'),
        ('en', 'English'),
    ]

    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text='Opsional. Mund të përdoret për login.'
    )
    username_changed_at = models.DateTimeField(blank=True, null=True)
    email = models.EmailField(
        _('email address'),
        unique=True,
        null=True,
        blank=True
    )
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_image = models.URLField(max_length=500, blank=True, null=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='regular')

    is_guest = models.BooleanField(default=False)
    guest_expires_at = models.DateTimeField(blank=True, null=True)

    # Email verification
    email_verification_code = models.CharField(max_length=6, blank=True, null=True)
    email_verification_code_sent_at = models.DateTimeField(blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)

    # Phone verification
    phone_verification_code = models.CharField(max_length=6, blank=True, null=True)
    phone_verification_code_sent_at = models.DateTimeField(blank=True, null=True)
    is_phone_verified = models.BooleanField(default=False)

    is_banned = models.BooleanField(default=False)
    ban_reason = models.TextField(blank=True, null=True)

    referral_code = models.CharField(max_length=20, unique=True, editable=False)
    referred_by = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='referrals'
    )

    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='sq')
    profile_visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='public')

    last_login = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        constraints = [
            # Business users: duhet email ose phone
            models.CheckConstraint(
                check=(
                    ~models.Q(user_type='business') |
                    models.Q(email__isnull=False) |
                    models.Q(phone__isnull=False)
                ),
                name='business_requires_email_or_phone'
            ),
            # Çdo user duhet të ketë email ose username
            models.CheckConstraint(
                check=(
                    models.Q(email__isnull=False) |
                    models.Q(username__isnull=False)
                ),
                name='user_requires_email_or_username'
            ),
        ]

    def __str__(self):
        return self.email or self.username or str(self.id)

    def clean(self):
        super().clean()
        if self.user_type == 'business' and not self.email and not self.phone:
            raise ValidationError(
                'Bizneset duhet të kenë të paktën email ose numër telefoni.'
            )
        if not self.email and not self.username:
            raise ValidationError(
                'Duhet të vendosni të paktën email ose username.'
            )

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        super().save(*args, **kwargs)

    @property
    def is_business_owner(self):
        return self.user_type == 'business' and self.businesses.exists()

    @property
    def primary_business(self):
        return self.businesses.filter(is_primary=True).first()

    @property
    def total_businesses(self):
        return self.businesses.count()

    @property
    def can_make_inquiry(self):
        """Regular users duhet email ose phone për inquiry"""
        if self.user_type == 'guest':
            return False
        if self.user_type == 'business':
            return True
        # Regular: duhet të paktën email ose phone
        return bool(self.email or self.phone)

    @staticmethod
    def generate_referral_code():
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not User.objects.filter(referral_code=code).exists():
                return code

    def generate_verification_code(self):
        """Generate 6-digit code"""
        import random
        return ''.join([str(random.randint(0, 9)) for _ in range(6)])

    def is_email_code_valid(self):
        """Check if email verification code hasn't expired"""
        if not self.email_verification_code_sent_at:
            return False
        from django.utils import timezone
        from django.conf import settings
        expiry = self.email_verification_code_sent_at + timezone.timedelta(
            minutes=settings.EMAIL_VERIFICATION_CODE_EXPIRY_MINUTES
        )
        return timezone.now() < expiry

    def is_phone_code_valid(self):
        """Check if phone verification code hasn't expired"""
        if not self.phone_verification_code_sent_at:
            return False
        from django.utils import timezone
        from django.conf import settings
        expiry = self.phone_verification_code_sent_at + timezone.timedelta(
            minutes=settings.PHONE_VERIFICATION_CODE_EXPIRY_MINUTES
        )
        return timezone.now() < expiry

    @classmethod
    def cleanup_expired_guests(cls):
        from django.utils import timezone
        expired = cls.objects.filter(
            is_guest=True,
            guest_expires_at__lt=timezone.now()
        )
        count = expired.count()
        expired.delete()
        return count


class BlockedUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    blocker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocking')
    blocked = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'blocked_users'
        unique_together = ['blocker', 'blocked']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.blocker} blocked {self.blocked}"


class OAuthToken(models.Model):
    PROVIDER_CHOICES = [
        ('google', 'Google'),
        ('facebook', 'Facebook'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='oauth_tokens')
    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES)
    access_token = models.TextField()
    refresh_token = models.TextField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'oauth_tokens'
        ordering = ['-created_at']