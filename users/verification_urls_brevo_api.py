# users/verification_urls.py

from django.urls import path
from . import verification_views_brevo_api

urlpatterns = [
    path('send-email-verification/',
         verification_views_brevo_api.send_email_verification,
         name='send-email-verification'),
    path('verify-email/',
         verification_views_brevo_api.verify_email_code,
         name='verify-email'),
    path('send-phone-verification/',
         verification_views_brevo_api.send_phone_verification,
         name='send-phone-verification'),
    path('verify-phone/',
         verification_views_brevo_api.verify_phone,
         name='verify-phone'),
]