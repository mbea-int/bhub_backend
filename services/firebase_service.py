# services/firebase_service.py (FILE E RE)

import os
import firebase_admin
from firebase_admin import credentials
import logging

logger = logging.getLogger(__name__)

def initialize_firebase():
    """Initialize Firebase Admin SDK (thirret vetëm një herë)"""
    if firebase_admin._apps:
        return  # Tashmë i inicializuar

    # Rruga drejt service account key
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cred_path = os.path.join(base_dir, 'firebase-service-account.json')

    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        logger.info("✅ Firebase Admin SDK initialized successfully")
    else:
        logger.error(
            f"❌ Firebase service account file not found at: {cred_path}"
        )
        raise FileNotFoundError(
            f"Firebase service account key not found: {cred_path}"
        )