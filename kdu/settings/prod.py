"""
Production settings — security hardened.
"""

from .base import *

DEBUG = False


# HTTPS enforcement
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_SSL_REDIRECT = True

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True


# Require all secrets from environment in production
if SECRET_KEY == "dev-only-insecure-change-me":
    raise RuntimeError("DJANGO_SECRET_KEY must be set in production.")
