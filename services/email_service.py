# core/services/email_service.py

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class BrevoEmailService:
    """Email service using Brevo (Sendinblue)"""

    def __init__(self):
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = settings.BREVO_API_KEY
        self.api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )

    def send_verification_code(self, to_email: str, code: str, user_name: str = '') -> bool:
        """Send email verification code"""
        try:
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=[{"email": to_email, "name": user_name}],
                sender={
                    "email": settings.BREVO_SENDER_EMAIL,
                    "name": settings.BREVO_SENDER_NAME,
                },
                subject="Kodi juaj i verifikimit - NYJA",
                html_content=self._build_verification_email(code, user_name),
            )

            response = self.api_instance.send_transac_email(send_smtp_email)
            logger.info(f"Verification email sent to {to_email}, message_id: {response.message_id}")
            return True

        except ApiException as e:
            logger.error(f"Brevo API error sending to {to_email}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending verification email to {to_email}: {e}")
            return False

    def _build_verification_email(self, code: str, user_name: str) -> str:
        """Build HTML email template"""
        name_display = user_name if user_name else 'Përdorues'

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
                .container {{ max-width: 480px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.08); }}
                .header {{ background: linear-gradient(135deg, #6366f1, #8b5cf6); padding: 32px; text-align: center; }}
                .header h1 {{ color: white; margin: 0; font-size: 24px; }}
                .body {{ padding: 32px; text-align: center; }}
                .code-box {{ background: #f8f9fa; border: 2px dashed #6366f1; border-radius: 12px; padding: 20px; margin: 24px 0; }}
                .code {{ font-size: 36px; font-weight: 800; letter-spacing: 8px; color: #6366f1; font-family: monospace; }}
                .note {{ color: #6b7280; font-size: 14px; margin-top: 24px; }}
                .footer {{ text-align: center; padding: 16px; color: #9ca3af; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 NYJA</h1>
                </div>
                <div class="body">
                    <p>Përshëndetje <strong>{name_display}</strong>,</p>
                    <p>Kodi juaj i verifikimit është:</p>
                    <div class="code-box">
                        <span class="code">{code}</span>
                    </div>
                    <p class="note">
                        Ky kod skadon pas <strong>15 minutash</strong>.<br>
                        Nëse nuk e keni kërkuar këtë kod, injoroni këtë email.
                    </p>
                </div>
                <div class="footer">
                    &copy; 2024 NYJA. Të gjitha të drejtat e rezervuara.
                </div>
            </div>
        </body>
        </html>
        """


# Singleton instance
brevo_email_service = BrevoEmailService()