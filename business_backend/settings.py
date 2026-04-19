import os
from pathlib import Path
from datetime import timedelta
from decouple import config
import cloudinary
import cloudinary.uploader
import cloudinary.api

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)

# Detect if running on PythonAnywhere
ON_PYTHONANYWHERE = "PYTHONANYWHERE_SITE" in os.environ or "pythonanywhere.com" in os.environ.get("PYTHONANYWHERE_DOMAIN", "")

# NGROK and ALLOWED_HOSTS Configuration
if DEBUG and not ON_PYTHONANYWHERE:
    NGROK_DOMAIN = 'b47a5b1de76c.ngrok-free.app'
    NGROK_URL = "https://2c19-31-22-48-65.ngrok-free.app"
    ALLOWED_HOSTS = [
        NGROK_DOMAIN,
        'localhost',
        '127.0.0.1',
        '10.218.234.148',
        '10.213.7.148',
        '10.90.56.45',
        '2c19-31-22-48-65.ngrok-free.app',
        'nyja.pythonanywhere.com'
    ]
else:
    NGROK_URL = None
    # For PythonAnywhere, add your username
    ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,2c19-31-22-48-65.ngrok-free.app').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'cloudinary',
    'cloudinary_storage',

    # Local apps
    'users',
    'businesses',
    'posts',
    'reviews',
    'groups',
    'notifications',
    'messaging',
    'reports',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'business_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'business_backend.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'sq'
TIME_ZONE = 'Europe/Tirane'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('sq', 'Albanian'),
    ('en', 'English'),
]

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Media files (using Cloudinary)
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME = config('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = config('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = config('CLOUDINARY_API_SECRET')

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': CLOUDINARY_CLOUD_NAME,
    'API_KEY': CLOUDINARY_API_KEY,
    'API_SECRET': CLOUDINARY_API_SECRET,
}

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
    secure=True
)

CLOUDINARY_DEFAULT_TRANSFORMATIONS = {
    'quality': 'auto:eco',
    'fetch_format': 'auto',
}

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    },
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# CORS Settings
if DEBUG and NGROK_URL:
    cors_origins = [
        'http://localhost:8000',
        'http://127.0.0.1:8000',
        'http://10.90.56.45:8000',
        'http://10.218.234.148:8000',
        'http://10.213.7.148:8000',
        'https://nyja.pythonanywhere.com',
        'https://2c19-31-22-48-65.ngrok-free.app',
        NGROK_URL
    ]
else:
    cors_origins = config('CORS_ALLOWED_ORIGINS', default='http://localhost:8000,https://a58e005e63e6.ngrok-free.app').split(',')

# CORS_ALLOWED_ORIGINS = cors_origins
CORS_ALLOW_ALL_ORIGINS = True
X_FRAME_OPTIONS = 'SAMEORIGIN'
CORS_ALLOW_CREDENTIALS = True

# Email Configuration (SendGrid)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = config('SENDGRID_API_KEY', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@muslimcommunity.al')

# Celery Configuration - DISABLED for PythonAnywhere free account
USE_CELERY = False
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Caching - Use file-based cache for PythonAnywhere
if ON_PYTHONANYWHERE:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
            'LOCATION': BASE_DIR / 'cache',
        }
    }
else:
    # Local development - use locmem cache
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }

# Rate Limiting - Disabled for PythonAnywhere free account
RATELIMIT_ENABLE = not ON_PYTHONANYWHERE
RATELIMIT_USE_CACHE = 'default' if not ON_PYTHONANYWHERE else None

# Logging
log_dir = BASE_DIR / 'logs'
log_dir.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': log_dir / 'django.log',
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'] if DEBUG else ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'apps': {
            'handlers': ['console'] if DEBUG else ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Security Settings (Production)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Content Moderation (Bad Words Filter)
CONTENT_FILTER_WORDS = []

# Business Settings
DEFAULT_MAX_POSTS_PER_DAY = 3
FREE_PREMIUM_SLOTS = 50
PREMIUM_PRICE_MONTHLY = 500  # in Lekë

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

cloudinary.config(
    cloud_name="YOUR_CLOUD_NAME",
    api_key="YOUR_API_KEY",
    api_secret="YOUR_API_SECRET",
    secure=True
)