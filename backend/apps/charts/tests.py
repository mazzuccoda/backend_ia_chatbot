import os

import pytest
from django.conf import settings
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestChartGeneration:
    def test_generate_bar_chart(self, auth_headers):
        client = APIClient()
        response = client.post(
            "/api/v1/charts/generate/",
            data={
                "chart_type": "bar",
                "title": "Test Chart",
                "x": ["A", "B", "C"],
                "y": [10, 20, 30],
                "unit": "USD",
            },
            format="json",
            **auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "chart_url" in data
        assert data["chart_url"].endswith(".png")

        # Verify file exists
        filepath = os.path.join(settings.MEDIA_ROOT, "charts", os.path.basename(data["chart_url"]))
        assert os.path.isfile(filepath)

    def test_invalid_chart_type(self, auth_headers):
        client = APIClient()
        response = client.post(
            "/api/v1/charts/generate/",
            data={"chart_type": "radar", "title": "X", "x": [1], "y": [1]},
            format="json",
            **auth_headers,
        )
        assert response.status_code == 400
        assert response.json()["error_code"] == "INVALID_CHART_TYPE"

    def test_missing_data(self, auth_headers):
        client = APIClient()
        response = client.post(
            "/api/v1/charts/generate/",
            data={"chart_type": "bar", "title": "X", "x": [], "y": []},
            format="json",
            **auth_headers,
        )
        assert response.status_code == 400
