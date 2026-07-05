"""Development settings — DEBUG=True, relaxed security."""

from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ["*"]

# Use browsable API in development
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
]
