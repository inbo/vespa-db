"""Load waarnemingen observations into the database."""

from typing import Any

from django.core.management.base import BaseCommand

from vespadb.observations.tasks.observation_sync import fetch_and_update_observations


class Command(BaseCommand):
    """Load waarnemingen observations into the database."""

    help = "Load waarnemingen observations into the database"

    def handle(self, *args: Any, **options: Any) -> None:
        """Load waarnemingen observations into the database."""
        sync_with_waarnemingen = input("Do you want to sync with waarnemingen.be? (yes/no): ")
        if sync_with_waarnemingen.lower() in {"yes", "y"}:
            since_week = int(input("Enter the number of weeks back to load observations: "))
            fetch_and_update_observations(since_week=since_week)
            self.stdout.write(self.style.SUCCESS("Observations loaded successfully"))
        else:
            self.stdout.write(self.style.SUCCESS("No observations loaded"))
        since_week = int(input("Enter the number of weeks back to load observations: "))
        fetch_and_update_observations(since_week=since_week)
        self.stdout.write(self.style.SUCCESS("Observations loaded successfully"))
