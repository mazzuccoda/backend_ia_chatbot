import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestApiKeyAuth:
    def test_request_without_api_key_is_rejected(self):
        client = APIClient()
        response = client.get("/api/v1/tools/")
        assert response.status_code == 403

    def test_request_with_invalid_key_is_rejected(self):
        client = APIClient()
        response = client.get("/api/v1/tools/", HTTP_X_API_KEY="bogus-key")
        assert response.status_code == 403

    def test_request_with_valid_key_but_wrong_scope(self, no_scope_headers):
        client = APIClient()
        response = client.get("/api/v1/tools/", **no_scope_headers)
        assert response.status_code == 403

    def test_request_with_valid_key_and_scope(self, auth_headers):
        client = APIClient()
        response = client.get("/api/v1/tools/", **auth_headers)
        assert response.status_code == 200
