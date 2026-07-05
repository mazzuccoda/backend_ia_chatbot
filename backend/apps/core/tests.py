import pytest
from django.test import TestCase
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestHealthCheck(TestCase):
    def test_health_returns_200_without_auth(self):
        client = APIClient()
        response = client.get("/api/v1/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("ok", "degraded")
        assert data["service"] == "analytics-backend"
        assert "version" in data
