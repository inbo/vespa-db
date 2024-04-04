"""Assign provinces to municipalities."""

from typing import Any

from django.core.management.base import BaseCommand

from vespadb.observations.models import Municipality, Province


class Command(BaseCommand):
    """Assign provinces to municipalities."""

    help = "Assign a province to each municipality based on their polygons"

    def handle(self, *args: Any, **options: Any) -> None:
        """Assign a province to each municipality based on their polygons."""
        for municipality in Municipality.objects.all():
            # Vind de provincie(s) waarvan de polygon intersecteert met de polygon van de gemeente
            provinces = Province.objects.filter(polygon__intersects=municipality.polygon)
            if provinces.exists():
                # Neem de eerste provincie in de lijst (of implementeer aanvullende logica als nodig)
                province = provinces.first()
                municipality.province = province
                municipality.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully assigned province {province.name} to municipality {municipality.name}"
                    )
                )
            else:
                self.stdout.write(self.style.WARNING(f"No province found for municipality {municipality.name}"))
