"""Management command to delete all records from the database."""

from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from vespadb.observations.models import Observation


class Command(BaseCommand):
    """Delete all records from the database."""

    help = "Delete all records from the database"

    def handle(self, *args: Any, **options: Any) -> None:
        """Handle the command to delete all records."""
        confirm = input(
            "Are you sure you want to delete all records from the database? This action cannot be undone! (yes/no): "
        )

        if confirm.lower() not in {"yes", "y"}:
            self.stdout.write(self.style.WARNING("Aborted. No records have been deleted."))
            return

        with transaction.atomic():
            count, _ = Observation.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f"Deleted {count} records from the Observation model."))

        self.stdout.write(self.style.SUCCESS("Operation completed."))
