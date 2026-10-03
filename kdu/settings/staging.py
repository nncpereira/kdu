"""
Local Docker test/staging environment settings.

Mirrors prod.py's deployment shape (gunicorn + nginx, built static
assets, Postgres) but WITHOUT the HTTPS-only hardening (SSL redirect,
HSTS, secure cookies) that prod.py forces unconditionally — this runs
over plain HTTP on localhost, not behind a real TLS-terminating domain.

Not to be confused with kdu/settings/test.py, which configures the
pytest run (disables migrations, fast password hashers) and is a
different thing entirely from this long-lived, seeded Docker env.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env.test")

from .base import *  # noqa: E402

DEBUG = False

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]

CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "http://localhost:8080").split(",")
    if o.strip()
]
CORS_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get("DJANGO_CORS_ALLOWED_ORIGINS", "http://localhost:8080").split(",")
    if o.strip()
]

# Database from env — points at the "db" Compose service, a separate
# Postgres instance/volume from both your native dev DB and prod.
DATABASES["default"] = {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": os.environ.get("POSTGRES_DB", "kdu_test"),
    "USER": os.environ.get("POSTGRES_USER", "kdu"),
    "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "kdu"),
    "HOST": os.environ.get("POSTGRES_HOST", "db"),
    "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    "CONN_MAX_AGE": 60,
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.request": {"level": "WARNING"},
    },
}

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
