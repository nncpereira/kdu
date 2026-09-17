"""
Development settings — DEBUG on, verbose logging.
"""

from .base import *

DEBUG = True
ALLOWED_HOSTS = ["*"]


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
