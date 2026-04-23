# users/token_views.py - VERSIONI FINAL

from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from .models import User
import logging

logger = logging.getLogger(__name__)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop(self.username_field, None)
        self.fields['identifier'] = serializers.CharField(
            write_only=True,
            help_text='Email ose username'
        )

    def validate(self, attrs):
        identifier = attrs.get('identifier', '').strip()
        password = attrs.get('password', '')

        if not identifier:
            raise AuthenticationFailed('Vendosni email ose username.')

        # ── Gjej user ──
        user = authenticate(
            request=self.context.get('request'),
            username=identifier,
            password=password,
        )

        if user is None:
            logger.warning(f"Login failed for: {identifier}")
            raise AuthenticationFailed(
                'Email/username ose fjalëkalimi i pavlefshëm.'
            )

        if not user.is_active:
            raise AuthenticationFailed('Llogaria është joaktive.')

        if user.is_banned:
            reason = f': {user.ban_reason}' if user.ban_reason else ''
            raise AuthenticationFailed(
                f'Llogaria juaj është bllokuar{reason}'
            )

        refresh = self.get_token(user)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer