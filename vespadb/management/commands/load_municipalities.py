from pathlib import Path
from typing import Any
from django.contrib.gis.utils import LayerMapping
from django.core.management.base import BaseCommand
from vespadb.observations.models import Municipality

municipality_mapping = {
    "oidn": "OIDN",
    "uidn": "UIDN",
    "terrid": "TERRID",
    "nis_code": "NISCODE",
    "name": "NAAM",
    "datpublbs": "DATPUBLBS",
    "numac": "NUMAC",
    "length": "LENGTE",
    "surface": "OPPERVL",
    "polygon": "MULTIPOLYGON",
}

class Command(BaseCommand):
    help = "Load and update a ShapeFile with municipality boundaries into the database."

    def handle(self, *args: Any, **options: Any) -> None:
        shapefile_path = str((Path(__file__).parent / "data" / "municipalities" / "Refgem.shp").resolve())
        lm = LayerMapping(Municipality, shapefile_path, municipality_mapping, transform=False, encoding="iso-8859-1")

        # Track NIS codes in the new shapefile to identify deletions
        new_nis_codes = set()

        # Process each feature in the shapefile
        for feature in lm.layer:
            attrs = lm.feature_kwargs(feature)
            nis_code = attrs["nis_code"]
            new_nis_codes.add(nis_code)

            # Check if municipality exists by nis_code
            municipality = Municipality.objects.filter(nis_code=nis_code).first()
            if municipality:
                # Update existing municipality
                for key, value in attrs.items():
                    setattr(municipality, key, value)
                municipality.save()
                self.stdout.write(
                    self.style.SUCCESS(f"Updated municipality '{attrs['name']}' (NIS: {nis_code})")
                )
            else:
                # Create new municipality
                municipality = Municipality(**attrs)
                municipality.save()
                self.stdout.write(
                    self.style.SUCCESS(f"Created municipality '{attrs['name']}' (NIS: {nis_code})")
                )

        # Delete municipalities not in shapefile
        deleted = Municipality.objects.exclude(nis_code__in=new_nis_codes).delete()
        if deleted[0] > 0:
            self.stdout.write(
                self.style.WARNING(f"Deleted {deleted[0]} municipalities not found in the new shapefile")
            )

        # Reassign provinces
        self.stdout.write(self.style.SUCCESS("Reassigning provinces to municipalities..."))
        self.run_assign_provinces()

    def run_assign_provinces(self):
        from django.core.management import call_command
        call_command("assign_provinces_to_municipalities")
