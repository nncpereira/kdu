"""
Production settings — security hardened.
"""

import os

from .base import *

DEBUG = False

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")
    if h.strip()
]

# HTTPS / security
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if o.strip()
]

# Static files via WhiteNoise
MIDDLEWARE.insert(
    1,  # right after SecurityMiddleware
    "whitenoise.middleware.WhiteNoiseMiddleware",
)
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# Require all secrets from environment in production
if SECRET_KEY == "dev-only-insecure-change-me":
    raise RuntimeError("DJANGO_SECRET_KEY must be set in production.")

# Secret from env
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

# Database from env
DATABASES["default"] = {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": os.environ["POSTGRES_DB"],
    "USER": os.environ["POSTGRES_USER"],
    "PASSWORD": os.environ["POSTGRES_PASSWORD"],
    "HOST": os.environ.get("POSTGRES_HOST", "db"),
    "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    "CONN_MAX_AGE": 60,
}

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.request": {"level": "WARNING"},
        "django.security": {"level": "WARNING"},
    },
}
