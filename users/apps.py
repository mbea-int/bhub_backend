from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        # Inicializo Firebase kur Django starton
        try:
            from services.firebase_service import initialize_firebase
            initialize_firebase()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(
                f"Firebase initialization skipped: {e}"
            )