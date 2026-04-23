# services/email_service_brevo_http.py

import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class BrevoHTTPEmailService:
    """
    Email service duke përdorur Brevo HTTP API direkt.
    Pa SDK - vetëm requests.
    Funksionon edhe në PythonAnywhere nëse api.brevo.com
    është në whitelist.
    """

    API_URL = 'https://api.brevo.com/v3/smtp/email'

    # Fallback: emri i vjetër (mund të jetë në whitelist)
    API_URL_LEGACY = 'https://api.sendinblue.com/v3/smtp/email'

    def send_verification_code(
            self, to_email: str, code: str, user_name: str = ''
    ) -> bool:
        try:
            api_key = settings.BREVO_API_KEY
            sender_email = settings.BREVO_SENDER_EMAIL
            sender_name = getattr(settings, 'BREVO_SENDER_NAME', 'NYJA')

            headers = {
                'accept': 'application/json',
                'api-key': api_key,
                'content-type': 'application/json',
            }

            payload = {
                'sender': {
                    'name': sender_name,
                    'email': sender_email,
                },
                'to': [
                    {
                        'email': to_email,
                        'name': user_name or 'Përdorues',
                    }
                ],
                'subject': 'Kodi juaj i verifikimit - NYJA',
                'htmlContent': self._build_verification_email(
                    code, user_name or 'Përdorues'
                ),
            }

            # Provo URL-në kryesore
            try:
                response = requests.post(
                    self.API_URL,
                    json=payload,
                    headers=headers,
                    timeout=30,
                )
            except requests.ConnectionError:
                # Fallback: provo URL-në legacy
                logger.warning(
                    "Brevo primary URL failed, trying legacy URL..."
                )
                response = requests.post(
                    self.API_URL_LEGACY,
                    json=payload,
                    headers=headers,
                    timeout=30,
                )

            if response.status_code in (200, 201):
                data = response.json()
                logger.info(
                    f"✅ Verification email sent to {to_email}, "
                    f"messageId: {data.get('messageId', 'N/A')}"
                )
                return True
            else:
                logger.error(
                    f"❌ Brevo API error {response.status_code}: "
                    f"{response.text}"
                )
                return False

        except requests.ConnectionError as e:
            logger.error(
                f"❌ Connection refused (PythonAnywhere whitelist?): {e}"
            )
            return False
        except Exception as e:
            logger.error(
                f"❌ Error sending verification email to {to_email}: {e}"
            )
            return False

    def _build_verification_email(self, code: str, name: str) -> str:
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f5;padding:32px 16px;">
        <tr>
            <td align="center">
                <table width="480" cellpadding="0" cellspacing="0" style="background:white;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
                    <tr>
                        <td style="background:linear-gradient(135deg,#6366f1,#8b5cf6);padding:32px;text-align:center;">
                            <h1 style="color:white;margin:0;font-size:28px;font-weight:800;">🔐 NYJA</h1>
                            <p style="color:rgba(255,255,255,0.8);margin:8px 0 0;font-size:14px;">Verifikimi i email-it</p>
                        </td>
                    </tr>
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


# Singleton
brevo_email_service = BrevoHTTPEmailService()