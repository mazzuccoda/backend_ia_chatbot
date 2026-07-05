"""DRF permission classes for API key + scope authentication."""

import logging

from rest_framework.permissions import BasePermission

from .models import ApiClient

logger = logging.getLogger(__name__)


class HasApiKey(BasePermission):
    """Require a valid X-API-Key header."""

    def has_permission(self, request, view):
        api_key = request.META.get("HTTP_X_API_KEY", "")
        if not api_key:
            return False
        client = ApiClient.authenticate(api_key)
        if client is None:
            return False
        request.api_client = client
        return True


class HasScope(BasePermission):
    """Require the API client to have a specific scope.

    Set `required_scope` on the view, e.g.:
        required_scope = "bot"
    """

    def has_permission(self, request, view):
        required = getattr(view, "required_scope", None)
        if required is None:
            return True
        client = getattr(request, "api_client", None)
        if client is None:
            return False
        return required in client.scopes
