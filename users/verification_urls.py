# users/verification_urls.py

from django.urls import path
from . import verification_views

urlpatterns = [
    path('send-email-verification/',
         verification_views.send_email_verification,
         name='send-email-verification'),
    path('verify-email/',
         verification_views.verify_email_code,
         name='verify-email'),
    path('verify-phone/',
         verification_views.verify_phone,
         name='verify-phone'),
    path('verification-status/',
         verification_views.verification_status,
         name='verification-status'),
]