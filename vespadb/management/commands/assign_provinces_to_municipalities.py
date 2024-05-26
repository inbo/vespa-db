"""Assign provinces to municipalities."""

from typing import Any

from django.core.management.base import BaseCommand

from vespadb.observations.models import Municipality, Province


class Command(BaseCommand):
    """Assign provinces to municipalities."""

    help = "Assign a province to each municipality based on their polygons"

    def handle(self, *args: Any, **options: Any) -> None:
        """Assign a province to each municipality based on their polygons."""
        unassigned_municipalities = Municipality.objects.filter(province__isnull=True)
        if not unassigned_municipalities.exists():
            self.stdout.write(
                self.style.SUCCESS("All municipalities already have a province assigned. No changes made.")
            )
            return

        for municipality in Municipality.objects.all():
            provinces = Province.objects.filter(polygon__intersects=municipality.polygon)

            if provinces.exists():
                if provinces.count() == 1:
                    province = provinces.first()
                else:
                    # Calculate intersection areas and choose the province with the largest intersection area
                    max_intersection_area = 0
                    chosen_province = None
                    for province in provinces:
                        intersection = municipality.polygon.intersection(province.polygon)
                        intersection_area = intersection.area
                        if intersection_area > max_intersection_area:
                            max_intersection_area = intersection_area
                            chosen_province = province
                    province = chosen_province

                municipality.province = province
                municipality.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully assigned province {province.name} to municipality {municipality.name}"
                    )
                )
            else:
                # Fallback to using the centroid if no intersections found
                centroid = municipality.polygon.centroid
                province = Province.objects.filter(polygon__contains=centroid).first()
                if province:
                    municipality.province = province
                    municipality.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Successfully assigned province {province.name} to municipality {municipality.name} using centroid"
                        )
                    )
                else:
                    self.stdout.write(self.style.WARNING(f"No province found for municipality {municipality.name}"))
