import pytest

from apps.auth_api.models import ApiClient


@pytest.fixture
def api_key():
    """Create an active API client and return the raw key."""
    raw_key = "test-api-key-for-pytest"
    ApiClient.objects.create(
        name="test-client",
        key_hash=ApiClient.hash_key(raw_key),
        scopes=["bot", "config_read"],
        is_active=True,
    )
    return raw_key


@pytest.fixture
def api_key_no_scope():
    """Create an API client with no scopes."""
    raw_key = "test-api-key-no-scope"
    ApiClient.objects.create(
        name="test-client-noscope",
        key_hash=ApiClient.hash_key(raw_key),
        scopes=[],
        is_active=True,
    )
    return raw_key


@pytest.fixture
def auth_headers(api_key):
    return {"HTTP_X_API_KEY": api_key}


@pytest.fixture
def no_scope_headers(api_key_no_scope):
    return {"HTTP_X_API_KEY": api_key_no_scope}
