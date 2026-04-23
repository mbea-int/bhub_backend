# services/email_service_brevo_http.py - RREGULLUAR

import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class BrevoHTTPEmailService:
    """Brevo HTTP API - pa SDK"""

    API_URL = 'https://api.brevo.com/v3/smtp/email'

    def send_verification_code(
        self, to_email: str, code: str, user_name: str = ''
    ) -> bool:
        try:
            headers = {
                'accept': 'application/json',
                'api-key': settings.BREVO_API_KEY,
                'content-type': 'application/json',
            }

            payload = {
                'sender': {
                    'name': getattr(settings, 'BREVO_SENDER_NAME', 'NYJA'),
                    'email': settings.BREVO_SENDER_EMAIL,
                },
                'to': [
                    {
                        'email': to_email,
                        'name': user_name or 'Përdorues',
                    }
                ],
                'subject': 'Kodi juaj i verifikimit - NYJA',
                'htmlContent': self._build_html(code, user_name or 'Përdorues'),
            }

            response = requests.post(
                self.API_URL,
                json=payload,
                headers=headers,
                timeout=30,
            )

            if response.status_code in (200, 201):
                logger.info(
                    f"✅ Email sent to {to_email}, "
                    f"response: {response.json()}"
                )
                return True
            else:
                logger.error(
                    f"❌ Brevo error {response.status_code}: {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"❌ Email error: {e}")
            return False

    def _build_html(self, code: str, name: str) -> str:
        return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f5;padding:32px 16px;">
<tr><td align="center">
<table width="480" cellpadding="0" cellspacing="0" style="background:white;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
<tr><td style="background:linear-gradient(135deg,#6366f1,#8b5cf6);padding:32px;text-align:center;">
<h1 style="color:white;margin:0;font-size:28px;">🔐 NYJA</h1>
</td></tr>
<tr><td style="padding:32px;text-align:center;">
<p style="color:#374151;font-size:16px;">Përshëndetje <strong>{name}</strong>,</p>
<p style="color:#6b7280;">Kodi juaj i verifikimit:</p>
<div style="background:#f8f9fa;border:2px dashed #6366f1;border-radius:12px;padding:24px;margin:20px auto;max-width:280px;">
<span style="font-size:40px;font-weight:800;letter-spacing:10px;color:#6366f1;font-family:monospace;">{code}</span>
</div>
<p style="color:#9ca3af;font-size:13px;">Skadon pas <strong>15 minutash</strong>.</p>
</td></tr>
<tr><td style="text-align:center;padding:16px;border-top:1px solid #f3f4f6;">
<p style="color:#9ca3af;font-size:12px;">&copy; 2024 NYJA</p>
</td></tr></table>
</td></tr></table></body></html>"""


brevo_email_service = BrevoHTTPEmailService()