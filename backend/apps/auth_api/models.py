import hashlib
import secrets

from django.db import models


class ApiClient(models.Model):
    """API client with scoped access control."""

    name = models.CharField(max_length=100)
    key_hash = models.CharField(max_length=64, unique=True, editable=False)
    scopes = models.JSONField(default=list, help_text='Lista de scopes, ej. ["bot", "config_read"]')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "API Client"
        verbose_name_plural = "API Clients"

    def __str__(self):
        return f"{self.name} (active={self.is_active})"

    @staticmethod
    def hash_key(raw_key: str) -> str:
        return hashlib.sha256(raw_key.encode()).hexdigest()

    @classmethod
    def create_with_key(cls, name: str, scopes: list[str] | None = None) -> tuple["ApiClient", str]:
        """Create a new ApiClient and return (instance, raw_key)."""
        raw_key = secrets.token_urlsafe(32)
        client = cls.objects.create(
            name=name,
            key_hash=cls.hash_key(raw_key),
            scopes=scopes or ["bot"],
        )
        return client, raw_key

    @classmethod
    def authenticate(cls, raw_key: str) -> "ApiClient | None":
        key_hash = cls.hash_key(raw_key)
        try:
            client = cls.objects.get(key_hash=key_hash, is_active=True)
            return client
        except cls.DoesNotExist:
            return None
