import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestMemory:
    def test_save_and_get_memory(self, auth_headers):
        client = APIClient()

        # Save
        response = client.post(
            "/api/v1/memory/save/",
            data={"user_id": "u1", "conversation_id": "c1", "key": "name", "value": "Daniel"},
            format="json",
            **auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["data"]["created"] is True

        # Update
        response = client.post(
            "/api/v1/memory/save/",
            data={"user_id": "u1", "conversation_id": "c1", "key": "name", "value": "Daniel M."},
            format="json",
            **auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["created"] is False

        # Get
        response = client.post(
            "/api/v1/memory/get/",
            data={"user_id": "u1", "conversation_id": "c1", "key": "name"},
            format="json",
            **auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "Daniel M."

    def test_get_all_keys(self, auth_headers):
        client = APIClient()
        client.post(
            "/api/v1/memory/save/",
            data={"user_id": "u2", "conversation_id": "c2", "key": "k1", "value": 1},
            format="json",
            **auth_headers,
        )
        client.post(
            "/api/v1/memory/save/",
            data={"user_id": "u2", "conversation_id": "c2", "key": "k2", "value": 2},
            format="json",
            **auth_headers,
        )
        response = client.post(
            "/api/v1/memory/get/",
            data={"user_id": "u2", "conversation_id": "c2"},
            format="json",
            **auth_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["k1"] == 1
        assert data["k2"] == 2
