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
            choice = input("Enter '1' to specify weeks back or '2' to specify a date (ddMMyyyy): ")
            if choice == "1":
                since_week = int(input("Enter the number of weeks back to load observations: "))
                fetch_and_update_observations(since_week=since_week)
            elif choice == "2":
                date = input("Enter the date (ddMMyyyy) to load observations from: ")
                fetch_and_update_observations(date=date)
            else:
                self.stdout.write(self.style.ERROR("Invalid choice. Please enter '1' or '2'."))
                return
            self.stdout.write(self.style.SUCCESS("Observations loaded successfully"))
        else:
            self.stdout.write(self.style.SUCCESS("No observations loaded"))
