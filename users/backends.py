# users/backends.py (FILE E RE)

from django.contrib.auth.backends import ModelBackend
from .models import User
import logging

logger = logging.getLogger(__name__)


class EmailOrUsernameBackend(ModelBackend):
    """
    Lejon autentifikim me email OSE username.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            return None

        user = None

        # Provo me email
        if '@' in username:
            try:
                user = User.objects.get(email__iexact=username)
            except User.DoesNotExist:
                pass

        # Provo me username
        if user is None:
            try:
                user = User.objects.get(username__iexact=username)
            except User.DoesNotExist:
                pass

        # Provo me email direkt (pa @ check - për rastin kur
        # email_for_auth dërgohet nga token_views)
        if user is None:
            try:
                user = User.objects.get(email__iexact=username)
            except User.DoesNotExist:
                return None

        # Verifiko password
        if user and user.check_password(password):
            if self.user_can_authenticate(user):
                return user

        return None