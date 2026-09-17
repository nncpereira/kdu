"""
Test settings — fast hashers, in-memory email, separate DB.
"""

from .base import *

DEBUG = False
TESTING = True


# Use a distinct test DB name so it never touches the dev DB
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_TEST_DB", "kdu_test"),
        "USER": os.environ.get("POSTGRES_USER", "kdu"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "kdu"),
        "HOST": os.environ.get("POSTGRES_HOST", "127.0.0.1"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        "TEST": {"NAME": "test_kdu"},
    }
}

# Keep tests fast
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Turn off localization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_TZ = True

# Suppress migration chatter
MIGRATION_MODULES = {}

# Celery tasks run synchronously in tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Email backend
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
