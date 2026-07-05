"""Healthcheck endpoint — no authentication required."""

import logging

from django.db import connections
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)

VERSION = "0.1.0"


class HealthCheckView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        db_status = "ok"
        try:
            connections["default"].ensure_connection()
        except Exception:
            db_status = "error"

        redis_status = None
        from django.conf import settings

        if settings.REDIS_URL:
            try:
                from django.core.cache import cache

                cache.set("_health", "1", 5)
                redis_status = "ok"
            except Exception:
                redis_status = "error"

        overall = "ok" if db_status == "ok" else "degraded"
        return Response(
            {
                "status": overall,
                "service": "analytics-backend",
                "database": db_status,
                "redis": redis_status,
                "version": VERSION,
            },
            status=status.HTTP_200_OK,
        )
