from pathlib import Path
from typing import Any
from django.contrib.gis.utils import LayerMapping
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from vespadb.observations.models import Municipality
import logging

logger = logging.getLogger(__name__)

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

        # Track NIS codes and names to identify duplicates and deletions
        new_nis_codes = set()
        seen_names = set()

        # Process each feature in the shapefile
        for feature in lm.layer:
            attrs = lm.feature_kwargs(feature)
            nis_code = attrs["nis_code"]
            name = attrs["name"]

            logger.debug(f"Processing feature: NIS={nis_code}, Name={name}")

            # Check for duplicate names in the shapefile
            if name in seen_names:
                logger.warning(f"Duplicate name '{name}' found in shapefile with NIS={nis_code}")
            seen_names.add(name)

            new_nis_codes.add(nis_code)

            # Check if municipality exists by nis_code
            municipality = Municipality.objects.filter(nis_code=nis_code).first()
            try:
                if municipality:
                    # Update existing municipality by nis_code
                    old_name = municipality.name
                    for key, value in attrs.items():
                        setattr(municipality, key, value)
                    municipality.save()
                    self.stdout.write(
                        self.style.SUCCESS(f"Updated municipality '{name}' (NIS: {nis_code}, was '{old_name}')")
                    )
                    logger.info(f"Updated municipality: NIS={nis_code}, Name={name}, Previous Name={old_name}")
                else:
                    # Check if a municipality with the same name exists
                    existing_by_name = Municipality.objects.filter(name=name).first()
                    if existing_by_name:
                        # Update existing municipality by name
                        old_nis_code = existing_by_name.nis_code
                        for key, value in attrs.items():
                            setattr(existing_by_name, key, value)
                        existing_by_name.save()
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Updated municipality '{name}' (NIS: {nis_code}, was NIS: {old_nis_code})"
                            )
                        )
                        logger.info(
                            f"Updated municipality by name: Name={name}, New NIS={nis_code}, Previous NIS={old_nis_code}"
                        )
                    else:
                        # Create new municipality
                        municipality = Municipality(**attrs)
                        municipality.save()
                        self.stdout.write(
                            self.style.SUCCESS(f"Created municipality '{name}' (NIS: {nis_code})")
                        )
                        logger.info(f"Created municipality: NIS={nis_code}, Name={name}")
            except IntegrityError as e:
                logger.error(f"IntegrityError saving municipality '{name}' (NIS: {nis_code}): {str(e)}")
                self.stdout.write(
                    self.style.ERROR(f"Failed to save '{name}' (NIS: {nis_code}): {str(e)}")
                )
                continue

        # Delete municipalities not in the new shapefile
        deleted = Municipality.objects.exclude(nis_code__in=new_nis_codes).delete()
        if deleted[0] > 0:
            self.stdout.write(
                self.style.WARNING(f"Deleted {deleted[0]} municipalities not found in the new shapefile")
            )
            logger.info(f"Deleted {deleted[0]} municipalities not in shapefile")

        # Reassign provinces
        self.stdout.write(self.style.SUCCESS("Reassigning provinces to municipalities..."))
        logger.info("Reassigning provinces to municipalities")
        self.run_assign_provinces()

    def run_assign_provinces(self):
        from django.core.management import call_command
        call_command("assign_provinces_to_municipalities")
