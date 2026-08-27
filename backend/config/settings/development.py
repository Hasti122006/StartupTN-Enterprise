import os

from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

CORS_ALLOW_ALL_ORIGINS = True

# Development-specific cookie settings (allow insecure cookies for localhost)
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# Keep Django and the scraper on the same MySQL database. SQLite remains an
# explicit opt-in for isolated local tests only.
if os.getenv("USE_SQLITE", "false").lower() == "true":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Fallback to MySQL if needed
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass
