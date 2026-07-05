"""Management command to create the default API client from N8N_API_KEY_SEED."""

import logging

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.auth_api.models import ApiClient

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Create default ApiClient from N8N_API_KEY_SEED if no clients exist"

    def handle(self, *args, **options):
        seed = settings.N8N_API_KEY_SEED
        if not seed:
            self.stdout.write(self.style.WARNING("N8N_API_KEY_SEED not set — skipping default API client creation."))
            return

        key_hash = ApiClient.hash_key(seed)
        if ApiClient.objects.filter(key_hash=key_hash).exists():
            self.stdout.write(self.style.SUCCESS("Default API client already exists."))
            return

        ApiClient.objects.create(
            name="n8n-default",
            key_hash=key_hash,
            scopes=["bot"],
            is_active=True,
        )
        self.stdout.write(self.style.SUCCESS("Default API client created successfully (scope: bot)."))
