"""
Development settings — DEBUG on, verbose logging.
"""

from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

from .base import *  # noqa: E402

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Always trust the local dev origins for CSRF/CORS, regardless of what
# .env happens to have (it's often copied from a prod-style template).
_DEV_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
CSRF_TRUSTED_ORIGINS = list(dict.fromkeys([*CSRF_TRUSTED_ORIGINS, *_DEV_ORIGINS]))
CORS_ALLOWED_ORIGINS = list(dict.fromkeys([*CORS_ALLOWED_ORIGINS, *_DEV_ORIGINS]))


# Verbose logging in development
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django.db.backends": {"level": "WARNING"},
        "ledger": {"level": "DEBUG"},
        "pipeline": {"level": "DEBUG"},
        "shu": {"level": "DEBUG"},
    },
}


# Email to console during development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
