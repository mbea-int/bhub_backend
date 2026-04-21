# users/verification_views.py

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from django.conf import settings
from django_ratelimit.decorators import ratelimit
from .models import User
from services.email_service import brevo_email_service
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@ratelimit(key='user', rate='3/10m', method='POST')
def send_email_verification(request):
    """Send verification code to user's email"""
    user = request.user

    if not user.email:
        return Response(
            {'detail': 'Nuk keni email të regjistruar.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if user.is_email_verified:
        return Response(
            {'detail': 'Email-i juaj është verifikuar tashmë.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check cooldown (don't send too frequently)
    if user.email_verification_code_sent_at:
        time_since = timezone.now() - user.email_verification_code_sent_at
        if time_since.total_seconds() < 60:
            remaining = 60 - int(time_since.total_seconds())
            return Response(
                {
                    'detail': f'Prisni {remaining} sekonda para se të dërgoni përsëri.',
                    'cooldown_seconds': remaining,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

    # Generate and save code
    code = user.generate_verification_code()
    user.email_verification_code = code
    user.email_verification_code_sent_at = timezone.now()
    user.save(update_fields=[
        'email_verification_code',
        'email_verification_code_sent_at'
    ])

    # Send email
    success = brevo_email_service.send_verification_code(
        to_email=user.email,
        code=code,
        user_name=user.full_name,
    )

    if success:
        logger.info(f"Verification email sent to {user.email}")
        return Response({
            'detail': 'Kodi i verifikimit u dërgua te email-i juaj.',
            'email': _mask_email(user.email),
            'expires_in_minutes': settings.EMAIL_VERIFICATION_CODE_EXPIRY_MINUTES,
        })
    else:
        return Response(
            {'detail': 'Gabim gjatë dërgimit të email-it. Provoni përsëri.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@ratelimit(key='user', rate='5/10m', method='POST')
def verify_email_code(request):
    """Verify the email verification code"""
    user = request.user
    code = request.data.get('code', '').strip()

    if not code:
        return Response(
            {'detail': 'Kodi është i detyrueshëm.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not user.email_verification_code:
        return Response(
            {'detail': 'Nuk ka kod aktiv. Dërgoni një kod të ri.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not user.is_email_code_valid():
        user.email_verification_code = None
        user.save(update_fields=['email_verification_code'])
        return Response(
            {'detail': 'Kodi ka skaduar. Dërgoni një kod të ri.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if user.email_verification_code != code:
        return Response(
            {'detail': 'Kodi nuk është i saktë.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Success - verify email
    user.is_email_verified = True
    user.email_verification_code = None
    user.email_verification_code_sent_at = None
    user.save(update_fields=[
        'is_email_verified',
        'email_verification_code',
        'email_verification_code_sent_at',
    ])

    logger.info(f"Email verified for user {user.email}")

    return Response({
        'detail': 'Email-i u verifikua me sukses!',
        'is_email_verified': True,
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def send_phone_verification(request):
    """
    Send phone verification code.
    For now, this is a placeholder - Firebase Phone Auth handles this on client side.
    """
    return Response({
        'detail': 'Verifikimi i telefonit bëhet përmes Firebase.',
        'method': 'firebase_phone_auth',
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def verify_phone(request):
    """Mark phone as verified (called after Firebase verification succeeds)"""
    user = request.user
    firebase_token = request.data.get('firebase_id_token')

    if not firebase_token:
        return Response(
            {'detail': 'Firebase token mungon.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # TODO: Verify Firebase token server-side
    # For MVP, trust the client
    user.is_phone_verified = True
    user.save(update_fields=['is_phone_verified'])

    return Response({
        'detail': 'Telefoni u verifikua me sukses!',
        'is_phone_verified': True,
    })


def _mask_email(email: str) -> str:
    """Mask email for display: t***@gmail.com"""
    if not email or '@' not in email:
        return email
    local, domain = email.split('@', 1)
    if len(local) <= 2:
        masked = local[0] + '***'
    else:
        masked = local[0] + '***' + local[-1]
    return f"{masked}@{domain}"