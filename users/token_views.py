from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Pranon 'identifier' (email ose username) në vend të vetëm email.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hiq fushën email, shto identifier
        self.fields.pop(self.username_field, None)
        self.fields['identifier'] = serializers.CharField(
            write_only=True,
            help_text='Email ose username'
        )

    def validate(self, attrs):
        identifier = attrs.get('identifier', '').strip()
        password = attrs.get('password', '')

        if not identifier:
            raise serializers.ValidationError(
                {'identifier': _('Vendosni email ose username.')}
            )

        user = authenticate(
            request=self.context.get('request'),
            username=identifier,
            password=password
        )

        if not user:
            raise serializers.ValidationError(
                {'detail': _('Email/username ose fjalëkalimi i pavlefshëm.')}
            )

        if not user.is_active:
            raise serializers.ValidationError(
                {'detail': _('Llogaria është joaktive.')}
            )

        if user.is_banned:
            reason = f': {user.ban_reason}' if user.ban_reason else ''
            raise serializers.ValidationError(
                {'detail': _('Llogaria juaj është bllokuar') + reason}
            )

        refresh = self.get_token(user)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer