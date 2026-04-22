# users/verification_views.py

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from django.conf import settings
from services.email_service import EmailService
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
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

    # Cooldown check - 60 sekonda mes dërgimeve
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

    # Send email via Django SMTP (Brevo)
    success = EmailService.send_verification_code(
        to_email=user.email,
        code=code,
        user_name=user.full_name,
    )

    if success:
        return Response({
            'detail': 'Kodi i verifikimit u dërgua te email-i juaj.',
            'email': _mask_email(user.email),
            'expires_in_minutes': settings.EMAIL_VERIFICATION_CODE_EXPIRY_MINUTES,
        })
    else:
        # Fshi kodin nëse dërgimi dështoi
        user.email_verification_code = None
        user.email_verification_code_sent_at = None
        user.save(update_fields=[
            'email_verification_code',
            'email_verification_code_sent_at'
        ])
        return Response(
            {'detail': 'Gabim gjatë dërgimit të email-it. Provoni përsëri.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def verify_email_code(request):
    """Verify the email verification code"""
    user = request.user
    code = request.data.get('code', '').strip()

    if not code:
        return Response(
            {'detail': 'Kodi është i detyrueshëm.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(code) != 6 or not code.isdigit():
        return Response(
            {'detail': 'Kodi duhet të jetë 6 shifra.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if user.is_email_verified:
        return Response(
            {'detail': 'Email-i është verifikuar tashmë.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not user.email_verification_code:
        return Response(
            {'detail': 'Nuk ka kod aktiv. Dërgoni një kod të ri.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check expiry
    if not user.is_email_code_valid():
        user.email_verification_code = None
        user.save(update_fields=['email_verification_code'])
        return Response(
            {'detail': 'Kodi ka skaduar. Dërgoni një kod të ri.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check code
    if user.email_verification_code != code:
        return Response(
            {'detail': 'Kodi nuk është i saktë.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # ✅ Success
    user.is_email_verified = True
    user.email_verification_code = None
    user.email_verification_code_sent_at = None
    user.save(update_fields=[
        'is_email_verified',
        'email_verification_code',
        'email_verification_code_sent_at',
    ])

    logger.info(f"✅ Email verified for user {user.email}")

    return Response({
        'detail': 'Email-i u verifikua me sukses!',
        'is_email_verified': True,
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def verification_status(request):
    """Get current verification status"""
    user = request.user
    return Response({
        'email': user.email,
        'is_email_verified': user.is_email_verified,
        'phone': user.phone,
        'is_phone_verified': getattr(user, 'is_phone_verified', False),
        'has_email': bool(user.email),
        'has_phone': bool(user.phone),
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def verify_phone(request):
    """
    Verify phone number via Firebase ID Token.

    Rrjedha:
    1. Flutter → Firebase Phone Auth → merr SMS → verifikon kodin
    2. Flutter merr Firebase ID Token
    3. Flutter dërgon ID Token këtu
    4. Django verifikon token-in me Firebase Admin SDK
    5. Django shënon numrin si të verifikuar
    """
    user = request.user
    firebase_id_token = request.data.get('firebase_id_token')

    if not firebase_id_token:
        return Response(
            {'detail': 'Firebase ID token mungon.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not user.phone:
        return Response(
            {'detail': 'Nuk keni numër telefoni të regjistruar.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if user.is_phone_verified:
        return Response({
            'detail': 'Telefoni është verifikuar tashmë.',
            'is_phone_verified': True,
        })

    try:
        from firebase_admin import auth as firebase_auth

        # Verifiko Firebase ID Token
        decoded_token = firebase_auth.verify_id_token(firebase_id_token)

        firebase_phone = decoded_token.get('phone_number')
        firebase_uid = decoded_token.get('uid')

        logger.info(
            f"📱 Firebase token decoded - "
            f"phone: {firebase_phone}, uid: {firebase_uid}"
        )

        if not firebase_phone:
            return Response(
                {'detail': 'Firebase token nuk përmban numër telefoni.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ── Krahaso numrin e telefonit ──
        # Pastro formatimin për krahasim
        def clean_phone(p):
            """Hiq hapësirat, vizat, kllapat"""
            return (p or '').replace(' ', '').replace('-', '') \
                .replace('(', '').replace(')', '')

        user_phone_clean = clean_phone(user.phone)
        firebase_phone_clean = clean_phone(firebase_phone)

        # Kontrollo përputhjen
        # Lejon: +355691234567 == 0691234567 (hiq 0 dhe shto prefix)
        phones_match = False

        if user_phone_clean == firebase_phone_clean:
            phones_match = True
        elif firebase_phone_clean.endswith(
                user_phone_clean.lstrip('0')
        ):
            phones_match = True
        elif user_phone_clean.endswith(
                firebase_phone_clean.lstrip('+').lstrip('0')
        ):
            phones_match = True

        if not phones_match:
            logger.warning(
                f"⚠️ Phone mismatch - "
                f"user: {user_phone_clean}, "
                f"firebase: {firebase_phone_clean}"
            )
            return Response(
                {
                    'detail': (
                        'Numri i verifikuar nuk përputhet me numrin '
                        'në profilin tuaj.'
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ Verifikimi i suksesshëm
        user.is_phone_verified = True
        # Ruaj numrin në formatin ndërkombëtar nga Firebase
        user.phone = firebase_phone
        user.save(update_fields=['is_phone_verified', 'phone'])

        logger.info(
            f"✅ Phone verified for user {user.id}: {firebase_phone}"
        )

        return Response({
            'detail': 'Telefoni u verifikua me sukses!',
            'is_phone_verified': True,
            'phone': firebase_phone,
        })

    except ImportError:
        logger.error("❌ firebase_admin not installed")
        return Response(
            {'detail': 'Firebase nuk është konfiguruar në server.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    except firebase_auth.InvalidIdTokenError:
        logger.warning("❌ Invalid Firebase token")
        return Response(
            {'detail': 'Token i pavlefshëm. Provoni përsëri.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    except firebase_auth.ExpiredIdTokenError:
        logger.warning("❌ Expired Firebase token")
        return Response(
            {'detail': 'Token ka skaduar. Provoni përsëri.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    except firebase_auth.CertificateFetchError:
        logger.error("❌ Firebase certificate fetch error")
        return Response(
            {'detail': 'Gabim komunikimi me Firebase. Provoni përsëri.'},
            status=status.HTTP_502_BAD_GATEWAY
        )

    except Exception as e:
        logger.error(f"❌ Phone verification error: {str(e)}")
        return Response(
            {'detail': f'Gabim gjatë verifikimit: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _mask_email(email: str) -> str:
    """t***r@gmail.com"""
    if not email or '@' not in email:
        return email or ''
    local, domain = email.split('@', 1)
    if len(local) <= 2:
        masked = local[0] + '***'
    else:
        masked = local[0] + '***' + local[-1]
    return f"{masked}@{domain}"