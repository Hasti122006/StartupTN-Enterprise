from datetime import timedelta
import os
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    SECRET_KEY=(str, 'unsafe-development-key-replace-me'),
    ALLOWED_HOSTS=(list, ['*']),
    CORS_ALLOWED_ORIGINS=(list, ['http://localhost:3000', 'http://127.0.0.1:3000']),
)

# Read backend-local .env
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=['http://localhost:3000', 'http://127.0.0.1:3000'])

# App definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party packages
    'rest_framework',
    'corsheaders',
    'django_filters',
    'drf_spectacular',
    'channels',

    # Local apps
    'apps.companies',
    'apps.jobs',
    'apps.logs',
    'apps.exports',
    'apps.scraper',
    'apps.core',
    'apps.marketing',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.middleware.RequestLoggingMiddleware',
]

ROOT_URLCONF = 'config.urls'

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

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("MYSQL_DATABASE"),
        "USER": os.getenv("MYSQL_USER"),
        "PASSWORD": os.getenv("MYSQL_PASSWORD"),
        "HOST": os.getenv("MYSQL_HOST", "localhost"),
        "PORT": int(os.getenv("MYSQL_PORT", "3306")),
        "OPTIONS": {
            "charset": "utf8mb4",
        },
    }
}

# Custom User Model - Disabled
# AUTH_USER_MODEL = 'accounts.User'

# Password validation - Disabled
# AUTH_PASSWORD_VALIDATORS = [
#     {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
#     {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
#     {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
#     {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
# ]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static & Media files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DATA_ROOT = BASE_DIR / 'data'
EXPORTS_PATH = env('EXPORT_PATH', default=str(DATA_ROOT / 'exports'))

# CORS settings
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Session and Cookie settings
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:3000']

# Authentication settings
LOGIN_URL = "/auth/login/"
LOGIN_REDIRECT_URL = "/dashboard/"

# DRF Settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# SimpleJWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'sub',
}

# Celery & Redis
from urllib.parse import quote

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
REDIS_DB = int(os.getenv('REDIS_DB', '0'))


def _build_redis_url(host: str, port: int, password: str, db: int) -> str:
    if password:
        return f"redis://:{quote(password, safe='')}@{host}:{port}/{db}"
    return f"redis://{host}:{port}/{db}"


DEFAULT_REDIS_URL = _build_redis_url(REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB)
REDIS_URL = os.getenv('REDIS_URL', DEFAULT_REDIS_URL)

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [REDIS_URL],
        },
    },
}

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', _build_redis_url(REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, 0))
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', _build_redis_url(REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, 1))
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# n8n Integration
N8N_WEBHOOK_URL = env('N8N_WEBHOOK_URL', default='http://localhost:8088/webhook/startuptn/scrape')
N8N_API_KEY = env('N8N_API_KEY', default='startuptn-secret-key-2026')
N8N_API_TOKEN = env('N8N_API_TOKEN', default=N8N_API_KEY)
N8N_API_AUTH_ENABLED = env.bool('N8N_API_AUTH_ENABLED', default=True)
DJANGO_API_URL = env('DJANGO_API_URL', default='http://localhost:8000')

# StartupTN and scraper settings
STARTUPTN_LOGIN_URL = env('STARTUPTN_LOGIN_URL', default='https://startuptn.in/login')
STARTUPTN_PROFILE_URL = env('STARTUPTN_PROFILE_URL', default='https://startuptn.in/ecosystem-info')
STARTUPTN_STORAGE_STATE = env('STARTUPTN_STORAGE_STATE', default=str(BASE_DIR / 'Temp' / '.runtime' / 'startuptn-auth-state.json'))
SCRAPER_BASE_URL = env('SCRAPER_BASE_URL', default='https://startuptn.in/ecosystem-info')
SCRAPER_START_PAGE = env.int('SCRAPER_START_PAGE', default=1)
SCRAPER_END_PAGE = env.int('SCRAPER_END_PAGE', default=0)
SCRAPER_WORKERS = env.int('SCRAPER_WORKERS', default=2)
SCRAPER_DELAY_MIN = env.float('SCRAPER_DELAY_MIN', default=1.0)
SCRAPER_DELAY_MAX = env.float('SCRAPER_DELAY_MAX', default=3.0)
SCRAPER_RETRY_COUNT = env.int('SCRAPER_RETRY_COUNT', default=3)
SCRAPER_TIMEOUT = env.int('SCRAPER_TIMEOUT', default=30)
SCRAPER_HEADLESS = env.bool('SCRAPER_HEADLESS', default=True)

# Swagger Docs Settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'StartupTN Enterprise Scraper API',
    'DESCRIPTION': 'Django 5.x REST API for StartupTN Company Data Scraper',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# Email settings
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='localhost')
EMAIL_PORT = env.int('EMAIL_PORT', default=1025)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=False)
EMAIL_USE_SSL = env.bool('EMAIL_USE_SSL', default=False)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='no-reply@startuptn.in')

