"""Audit log creation and idempotency helpers."""

import logging
import time

from django.conf import settings
from django.utils import timezone

from .models import AuditLog

logger = logging.getLogger(__name__)


def check_idempotency(idempotency_key: str | None, endpoint: str) -> AuditLog | None:
    """Return cached AuditLog if idempotency key was already used within TTL."""
    if not idempotency_key:
        return None
    ttl = settings.IDEMPOTENCY_CACHE_TTL_SECONDS
    cutoff = timezone.now() - timezone.timedelta(seconds=ttl)
    try:
        return AuditLog.objects.get(
            idempotency_key=idempotency_key,
            endpoint=endpoint,
            created_at__gte=cutoff,
        )
    except AuditLog.DoesNotExist:
        return None


def create_audit_log(
    *,
    user_id: str = "",
    conversation_id: str = "",
    message: str | None = None,
    intent: str = "",
    tool_used: str = "",
    input_payload: dict | None = None,
    output_payload: dict | None = None,
    sql_generated: str | None = None,
    status: str = "ok",
    error_code: str | None = None,
    execution_time_ms: int = 0,
    idempotency_key: str | None = None,
    endpoint: str = "",
) -> AuditLog:
    return AuditLog.objects.create(
        user_id=user_id,
        conversation_id=conversation_id,
        message=message,
        intent=intent,
        tool_used=tool_used,
        input_payload=input_payload or {},
        output_payload=output_payload or {},
        sql_generated=sql_generated,
        status=status,
        error_code=error_code,
        execution_time_ms=execution_time_ms,
        idempotency_key=idempotency_key,
        endpoint=endpoint,
    )


class AuditTimer:
    """Context manager to measure execution time in milliseconds."""

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.elapsed_ms = int((time.perf_counter() - self.start) * 1000)
