import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auth_api.permissions import HasApiKey, HasScope

from .services import generate_chart

logger = logging.getLogger(__name__)

VALID_CHART_TYPES = {"bar", "line", "pie", "horizontal_bar"}


class ChartGenerateView(APIView):
    permission_classes = [HasApiKey, HasScope]
    required_scope = "bot"

    def post(self, request):
        chart_type = request.data.get("chart_type", "")
        title = request.data.get("title", "Chart")
        x = request.data.get("x", [])
        y = request.data.get("y", [])
        unit = request.data.get("unit", "")
        fmt = request.data.get("format", "png")

        if chart_type not in VALID_CHART_TYPES:
            return Response(
                {
                    "status": "error",
                    "error_code": "INVALID_CHART_TYPE",
                    "message": f"chart_type must be one of: {', '.join(VALID_CHART_TYPES)}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not x or not y:
            return Response(
                {"status": "error", "error_code": "MISSING_DATA", "message": "Both 'x' and 'y' are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = generate_chart(chart_type=chart_type, title=title, x=x, y=y, unit=unit, format=fmt)
        http_status = status.HTTP_200_OK if result["status"] == "ok" else status.HTTP_400_BAD_REQUEST
        return Response(result, status=http_status)
