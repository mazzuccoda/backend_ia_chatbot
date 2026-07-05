"""Production settings — secure defaults."""

from .base import *  # noqa: F401, F403

DEBUG = False

# Enforce HTTPS headers behind reverse proxy
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
