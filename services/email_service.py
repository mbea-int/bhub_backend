# core/services/email_service.py

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Email service using Django SMTP (Brevo)"""

    @staticmethod
    def send_verification_code(to_email: str, code: str, user_name: str = '') -> bool:
        """Send email verification code"""
        try:
            name_display = user_name or 'Përdorues'

            subject = 'Kodi juaj i verifikimit - NYJA'

            # Plain text version
            plain_message = (
                f'Përshëndetje {name_display},\n\n'
                f'Kodi juaj i verifikimit është: {code}\n\n'
                f'Ky kod skadon pas {settings.EMAIL_VERIFICATION_CODE_EXPIRY_MINUTES} minutash.\n'
                f'Nëse nuk e keni kërkuar këtë kod, injoroni këtë email.\n\n'
                f'- Ekipi NYJA'
            )

            # HTML version
            html_message = EmailService._build_verification_html(code, name_display)

            sent = send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                html_message=html_message,
                fail_silently=False,
            )

            if sent:
                logger.info(f"✅ Verification email sent to {to_email}")
                return True
            else:
                logger.error(f"❌ send_mail returned 0 for {to_email}")
                return False

        except Exception as e:
            logger.error(f"❌ Error sending verification email to {to_email}: {e}")
            return False

    @staticmethod
    def send_welcome_email(to_email: str, user_name: str = '') -> bool:
        """Send welcome email after registration"""
        try:
            name_display = user_name or 'Përdorues'

            subject = 'Mirësevini në NYJA! 🎉'

            plain_message = (
                f'Përshëndetje {name_display},\n\n'
                f'Mirësevini në NYJA! Llogaria juaj u krijua me sukses.\n\n'
                f'- Ekipi NYJA'
            )

            html_message = EmailService._build_welcome_html(name_display)

            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                html_message=html_message,
                fail_silently=True,
            )

            logger.info(f"✅ Welcome email sent to {to_email}")
            return True

        except Exception as e:
            logger.error(f"❌ Error sending welcome email to {to_email}: {e}")
            return False

    @staticmethod
    def send_password_reset_code(to_email: str, code: str, user_name: str = '') -> bool:
        """Send password reset code"""
        try:
            name_display = user_name or 'Përdorues'

            subject = 'Rivendosni fjalëkalimin - NYJA'

            plain_message = (
                f'Përshëndetje {name_display},\n\n'
                f'Kodi për rivendosjen e fjalëkalimit: {code}\n\n'
                f'Ky kod skadon pas 15 minutash.\n'
                f'Nëse nuk e keni kërkuar, injoroni këtë email.\n\n'
                f'- Ekipi NYJA'
            )

            html_message = EmailService._build_reset_html(code, name_display)

            sent = send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                html_message=html_message,
                fail_silently=False,
            )

            return bool(sent)

        except Exception as e:
            logger.error(f"❌ Error sending reset email to {to_email}: {e}")
            return False

    # ═══════════════════════════════════════════
    # ─── HTML Templates ───
    # ═══════════════════════════════════════════

    @staticmethod
    def _build_verification_html(code: str, name: str) -> str:
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f5;padding:32px 16px;">
        <tr>
            <td align="center">
                <table width="480" cellpadding="0" cellspacing="0" style="background:white;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
                    <!-- Header -->
                    <tr>
                        <td style="background:linear-gradient(135deg,#6366f1,#8b5cf6);padding:32px;text-align:center;">
                            <h1 style="color:white;margin:0;font-size:28px;font-weight:800;">🔐 NYJA</h1>
                            <p style="color:rgba(255,255,255,0.8);margin:8px 0 0;font-size:14px;">Verifikimi i email-it</p>
                        </td>
                    </tr>
                    <!-- Body -->
                    <tr>
                        <td style="padding:32px;text-align:center;">
                            <p style="color:#374151;font-size:16px;margin:0 0 8px;">Përshëndetje <strong>{name}</strong>,</p>
                            <p style="color:#6b7280;font-size:15px;margin:0 0 24px;">Kodi juaj i verifikimit është:</p>

                            <div style="background:#f8f9fa;border:2px dashed #6366f1;border-radius:12px;padding:24px;margin:0 auto;max-width:280px;">
                                <span style="font-size:40px;font-weight:800;letter-spacing:10px;color:#6366f1;font-family:monospace;">{code}</span>
                            </div>

                            <p style="color:#9ca3af;font-size:13px;margin:24px 0 0;line-height:1.6;">
                                Ky kod skadon pas <strong>15 minutash</strong>.<br>
                                Nëse nuk e keni kërkuar, injoroni këtë email.
                            </p>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="text-align:center;padding:16px;border-top:1px solid #f3f4f6;">
                            <p style="color:#9ca3af;font-size:12px;margin:0;">&copy; 2024 NYJA. Të gjitha të drejtat e rezervuara.</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

    @staticmethod
    def _build_welcome_html(name: str) -> str:
        return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f5;padding:32px 16px;">
        <tr>
            <td align="center">
                <table width="480" cellpadding="0" cellspacing="0" style="background:white;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
                    <tr>
                        <td style="background:linear-gradient(135deg,#6366f1,#8b5cf6);padding:32px;text-align:center;">
                            <h1 style="color:white;margin:0;font-size:28px;">🎉 Mirësevini!</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding:32px;text-align:center;">
                            <p style="color:#374151;font-size:18px;font-weight:600;">Përshëndetje {name}!</p>
                            <p style="color:#6b7280;font-size:15px;line-height:1.6;">
                                Llogaria juaj në NYJA u krijua me sukses.<br>
                                Tani mund të eksploroni biznese, produkte dhe shumë më tepër!
                            </p>
                            <div style="margin:24px 0;">
                                <a href="#" style="background:#6366f1;color:white;padding:14px 32px;border-radius:10px;text-decoration:none;font-weight:600;font-size:16px;">Hap aplikacionin</a>
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <td style="text-align:center;padding:16px;border-top:1px solid #f3f4f6;">
                            <p style="color:#9ca3af;font-size:12px;margin:0;">&copy; 2024 NYJA</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

    @staticmethod
    def _build_reset_html(code: str, name: str) -> str:
        return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f5;padding:32px 16px;">
        <tr>
            <td align="center">
                <table width="480" cellpadding="0" cellspacing="0" style="background:white;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
                    <tr>
                        <td style="background:linear-gradient(135deg,#ef4444,#f97316);padding:32px;text-align:center;">
                            <h1 style="color:white;margin:0;font-size:28px;">🔑 NYJA</h1>
                            <p style="color:rgba(255,255,255,0.8);margin:8px 0 0;">Rivendosja e fjalëkalimit</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding:32px;text-align:center;">
                            <p style="color:#374151;font-size:16px;">Përshëndetje <strong>{name}</strong>,</p>
                            <p style="color:#6b7280;font-size:15px;">Kodi për rivendosjen e fjalëkalimit:</p>
                            <div style="background:#fef2f2;border:2px dashed #ef4444;border-radius:12px;padding:24px;margin:20px auto;max-width:280px;">
                                <span style="font-size:40px;font-weight:800;letter-spacing:10px;color:#ef4444;font-family:monospace;">{code}</span>
                            </div>
                            <p style="color:#9ca3af;font-size:13px;">Skadon pas <strong>15 minutash</strong>.</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="text-align:center;padding:16px;border-top:1px solid #f3f4f6;">
                            <p style="color:#9ca3af;font-size:12px;">&copy; 2024 NYJA</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""