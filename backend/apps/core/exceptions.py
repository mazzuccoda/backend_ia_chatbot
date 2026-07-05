"""Custom DRF exception handler for consistent JSON responses."""

import logging

from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        data = {
            "status": "error",
            "error_code": response.status_code,
            "message": str(exc.detail) if hasattr(exc, "detail") else str(exc),
            "details": {},
        }
        response.data = data
    return response
