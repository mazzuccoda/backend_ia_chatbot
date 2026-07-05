"""Base Django settings shared by all environments."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "insecure-dev-key-change-me")

DEBUG = False

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,backend").split(",")

INSTALLED_APPS = [
    "admin_interface",
    "colorfield",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "rest_framework",
    "drf_spectacular",
    # Local apps
    "apps.core",
    "apps.auth_api",
    "apps.memory",
    "apps.audit",
    "apps.tools",
    "apps.analytics",
    "apps.charts",
    "apps.sqlsafe",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database
_db_url = os.environ.get("DATABASE_URL", "postgres://analytics_user:analytics_password@postgres:5432/analytics_bot")

def _parse_db_url(url: str) -> dict:
    """Parse a postgres:// URL into Django DATABASES dict."""
    import re
    m = re.match(r"postgres(?:ql)?://(?P<user>[^:]+):(?P<pw>[^@]+)@(?P<host>[^:]+):(?P<port>\d+)/(?P<name>.+)", url)
    if not m:
        return {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "analytics_bot",
            "USER": "analytics_user",
            "PASSWORD": "analytics_password",
            "HOST": "postgres",
            "PORT": "5432",
        }
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": m.group("name"),
        "USER": m.group("user"),
        "PASSWORD": m.group("pw"),
        "HOST": m.group("host"),
        "PORT": m.group("port"),
    }

_default_db = _parse_db_url(_db_url)

DATABASES = {
    "default": _default_db,
    "readonly": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _default_db["NAME"],
        "USER": os.environ.get("READONLY_DB_USER", "analytics_readonly"),
        "PASSWORD": os.environ.get("READONLY_DB_PASSWORD", "change-me"),
        "HOST": _default_db["HOST"],
        "PORT": _default_db["PORT"],
        "OPTIONS": {
            "options": f"-c statement_timeout={os.environ.get('FLEXIBLE_QUERY_TIMEOUT_SECONDS', '8')}s",
        },
    },
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es"
TIME_ZONE = "America/Argentina/Buenos_Aires"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = os.environ.get("MEDIA_URL", "/media/")
MEDIA_ROOT = os.environ.get("MEDIA_ROOT", str(BASE_DIR / "media"))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# DRF
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "EXCEPTION_HANDLER": "apps.core.exceptions.custom_exception_handler",
}

# drf-spectacular
SPECTACULAR_SETTINGS = {
    "TITLE": "Analytics Backend API",
    "DESCRIPTION": "Backend Django para bot de WhatsApp/n8n — herramientas analíticas",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# Redis (optional)
REDIS_URL = os.environ.get("REDIS_URL", "")

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

if REDIS_URL:
    try:
        CACHES["default"] = {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
        }
    except Exception:
        pass

# App-specific settings
IDEMPOTENCY_CACHE_TTL_SECONDS = int(os.environ.get("IDEMPOTENCY_CACHE_TTL_SECONDS", "86400"))
CHART_MAX_WIDTH_PX = int(os.environ.get("CHART_MAX_WIDTH_PX", "1080"))
CHART_DEFAULT_DPI = int(os.environ.get("CHART_DEFAULT_DPI", "150"))
FLEXIBLE_QUERY_LLM_PROVIDER = os.environ.get("FLEXIBLE_QUERY_LLM_PROVIDER", "openai")
FLEXIBLE_QUERY_LLM_MODEL = os.environ.get("FLEXIBLE_QUERY_LLM_MODEL", "gpt-4o-mini")
FLEXIBLE_QUERY_LLM_API_KEY = os.environ.get("FLEXIBLE_QUERY_LLM_API_KEY", "")
FLEXIBLE_QUERY_MIN_CONFIDENCE = float(os.environ.get("FLEXIBLE_QUERY_MIN_CONFIDENCE", "0.6"))
FLEXIBLE_QUERY_TIMEOUT_SECONDS = int(os.environ.get("FLEXIBLE_QUERY_TIMEOUT_SECONDS", "8"))
N8N_API_KEY_SEED = os.environ.get("N8N_API_KEY_SEED", "")

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
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "apps": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
    },
}

# django-admin-interface: allow iframe embedding for admin
X_FRAME_OPTIONS = "SAMEORIGIN"
SILENCED_SYSTEM_CHECKS = ["security.W019"]
