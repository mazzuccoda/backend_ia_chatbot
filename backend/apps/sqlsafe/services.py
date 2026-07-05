"""Service layer for consulta_flexible endpoint."""

import logging

from apps.audit.services import AuditTimer, create_audit_log

from .read_replica import ejecutar_en_readonly
from .text_to_sql import generar_sql
from .validators import validar_sql

logger = logging.getLogger(__name__)


def ejecutar_consulta_flexible(
    *,
    message: str,
    user_id: str = "",
    conversation_id: str = "",
    idempotency_key: str | None = None,
    endpoint: str = "consulta-flexible",
) -> dict:
    """Full flow: generate SQL, validate, execute on readonly connection."""
    from django.conf import settings

    min_confidence = settings.FLEXIBLE_QUERY_MIN_CONFIDENCE

    with AuditTimer() as timer:
        # Step 1: Generate SQL
        gen_result = generar_sql(message)
        confianza = gen_result.get("confianza", 0.0)

        if confianza < min_confidence:
            audit = create_audit_log(
                user_id=user_id,
                conversation_id=conversation_id,
                message=message,
                tool_used="consulta_flexible",
                input_payload={"message": message},
                output_payload=gen_result,
                status="low_confidence",
                error_code="UNSUPPORTED",
                execution_time_ms=0,
                idempotency_key=idempotency_key,
                endpoint=endpoint,
            )
            return {
                "status": "error",
                "error_code": "UNSUPPORTED",
                "message": "No matching metric found or low confidence.",
                "audit_id": audit.id,
            }

        sql = gen_result.get("sql", "")

        # Step 2: Validate SQL
        validation = validar_sql(sql)
        if not validation["valido"]:
            audit = create_audit_log(
                user_id=user_id,
                conversation_id=conversation_id,
                message=message,
                tool_used="consulta_flexible",
                input_payload={"message": message},
                output_payload=validation,
                sql_generated=sql,
                status="rejected",
                error_code="INVALID_QUERY",
                execution_time_ms=0,
                idempotency_key=idempotency_key,
                endpoint=endpoint,
            )
            return {
                "status": "error",
                "error_code": "INVALID_QUERY",
                "message": validation["error"],
                "audit_id": audit.id,
            }

        sql_final = validation["sql_final"]

        # Step 3: Execute on readonly connection
        try:
            rows = ejecutar_en_readonly(sql_final)
        except Exception as exc:
            error_str = str(exc)
            is_timeout = "canceling statement due to statement timeout" in error_str.lower() or "timeout" in error_str.lower()
            status_val = "timeout" if is_timeout else "error"
            error_code = "TIMEOUT" if is_timeout else "EXECUTION_ERROR"

            audit = create_audit_log(
                user_id=user_id,
                conversation_id=conversation_id,
                message=message,
                tool_used="consulta_flexible",
                input_payload={"message": message},
                sql_generated=sql_final,
                status=status_val,
                error_code=error_code,
                execution_time_ms=0,
                idempotency_key=idempotency_key,
                endpoint=endpoint,
            )
            return {
                "status": "error",
                "error_code": error_code,
                "message": error_str,
                "audit_id": audit.id,
            }

    audit = create_audit_log(
        user_id=user_id,
        conversation_id=conversation_id,
        message=message,
        tool_used="consulta_flexible",
        input_payload={"message": message},
        output_payload={"row_count": len(rows)},
        sql_generated=sql_final,
        status="ok",
        execution_time_ms=timer.elapsed_ms,
        idempotency_key=idempotency_key,
        endpoint=endpoint,
    )
    return {
        "status": "ok",
        "data": rows,
        "sql_ejecutado": sql_final,
        "audit_id": audit.id,
    }
