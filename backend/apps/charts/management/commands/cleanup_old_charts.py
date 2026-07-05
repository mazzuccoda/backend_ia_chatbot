"""Remove chart files older than N days."""

import logging
import os
import time

from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Delete chart image files older than --days (default 7)"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=7, help="Delete charts older than this many days")

    def handle(self, *args, **options):
        days = options["days"]
        charts_dir = os.path.join(settings.MEDIA_ROOT, "charts")
        if not os.path.isdir(charts_dir):
            self.stdout.write("Charts directory does not exist — nothing to clean.")
            return

        cutoff = time.time() - (days * 86400)
        removed = 0
        for filename in os.listdir(charts_dir):
            filepath = os.path.join(charts_dir, filename)
            if os.path.isfile(filepath) and os.path.getmtime(filepath) < cutoff:
                os.remove(filepath)
                removed += 1

        self.stdout.write(self.style.SUCCESS(f"Removed {removed} chart(s) older than {days} day(s)."))
