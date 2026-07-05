"""Tool views: catalog listing, generic metric execution, flexible query."""

import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services import AuditTimer, check_idempotency, create_audit_log
from apps.auth_api.permissions import HasApiKey, HasScope
from apps.sqlsafe.generic_lookup import ejecutar_metrica_determinista
from apps.sqlsafe.models import Metrica
from apps.sqlsafe.services import ejecutar_consulta_flexible

logger = logging.getLogger(__name__)


class ToolCatalogView(APIView):
    """GET /api/v1/tools/ — list all active deterministic tools."""

    permission_classes = [HasApiKey, HasScope]
    required_scope = "bot"

    def get(self, request):
        metricas = (
            Metrica.objects.filter(activa=True, expone_tool_determinista=True)
            .prefetch_related("dimensiones")
        )
        tools = []
        for m in metricas:
            required_params = []
            optional_params = []
            for d in m.dimensiones.all():
                param_info = {"name": d.nombre, "type": d.tipo, "column": d.columna}
                if d.requerido:
                    required_params.append(param_info)
                else:
                    optional_params.append(param_info)

            output_fields = [m.medida_alias]
            if m.unidad_columna:
                output_fields.append("unit")
            if m.moneda_columna:
                output_fields.append("currency")

            tools.append({
                "name": m.nombre,
                "description": m.descripcion,
                "required_params": required_params,
                "optional_params": optional_params,
                "output_schema": output_fields,
            })

        return Response({"status": "ok", "data": tools})


class ToolRunView(APIView):
    """POST /api/v1/tools/<nombre_metrica>/ — execute a deterministic metric."""

    permission_classes = [HasApiKey, HasScope]
    required_scope = "bot"

    def post(self, request, nombre_metrica):
        idempotency_key = request.META.get("HTTP_IDEMPOTENCY_KEY")
        endpoint = f"tools/{nombre_metrica}"

        # Check idempotency
        cached = check_idempotency(idempotency_key, endpoint)
        if cached is not None:
            return Response(cached.output_payload, status=status.HTTP_200_OK)

        params = request.data or {}
        user_id = params.pop("user_id", "")
        conversation_id = params.pop("conversation_id", "")
        message_text = params.pop("message", None)

        with AuditTimer() as timer:
            result = ejecutar_metrica_determinista(nombre_metrica, params)

        audit = create_audit_log(
            user_id=user_id,
            conversation_id=conversation_id,
            message=message_text,
            tool_used=nombre_metrica,
            input_payload=params,
            output_payload=result,
            status=result.get("status", "error"),
            error_code=result.get("error_code"),
            execution_time_ms=timer.elapsed_ms,
            idempotency_key=idempotency_key,
            endpoint=endpoint,
        )
        result["audit_id"] = audit.id

        http_status = status.HTTP_200_OK if result["status"] == "ok" else status.HTTP_400_BAD_REQUEST
        return Response(result, status=http_status)


class ConsultaFlexibleView(APIView):
    """POST /api/v1/tools/consulta-flexible/ — text-to-SQL fallback."""

    permission_classes = [HasApiKey, HasScope]
    required_scope = "bot"

    def post(self, request):
        message = request.data.get("message", "")
        user_id = request.data.get("user_id", "")
        conversation_id = request.data.get("conversation_id", "")
        idempotency_key = request.META.get("HTTP_IDEMPOTENCY_KEY")
        endpoint = "tools/consulta-flexible"

        if not message:
            return Response(
                {"status": "error", "error_code": "MISSING_MESSAGE", "message": "Field 'message' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check idempotency
        cached = check_idempotency(idempotency_key, endpoint)
        if cached is not None:
            return Response(cached.output_payload, status=status.HTTP_200_OK)

        result = ejecutar_consulta_flexible(
            message=message,
            user_id=user_id,
            conversation_id=conversation_id,
            idempotency_key=idempotency_key,
            endpoint=endpoint,
        )

        http_status = status.HTTP_200_OK if result.get("status") == "ok" else status.HTTP_400_BAD_REQUEST
        return Response(result, status=http_status)
