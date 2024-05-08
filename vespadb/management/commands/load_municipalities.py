"""Handlers."""

from pathlib import Path
from typing import Any

from django.contrib.gis.utils import LayerMapping
from django.core.management.base import BaseCommand

from vespadb.observations.models import Municipality

# A mapping dictionary to map field names from the Shapefile to the Municipality model fields.
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
    """A custom management command that loads a ShapeFile containing municipality boundaries into the database.

    This command uses the LayerMapping utility from Django's GIS framework to perform the data import.
    """

    help: str = "Laadt een ShapeFile met gemeentegrenzen in de database."

    def handle(self, *args: Any, **options: Any) -> None:
        """
        Handle municipality data loading.

        :param args: Variable length argument list.
        :param options: Arbitrary keyword arguments.
        """
        if Municipality.objects.exists():
            self.stdout.write(self.style.SUCCESS("Municipality data already exists in the database. No changes made."))
            return

        shapefile_path: str = str((Path(__file__).parent / "data" / "municipalities" / "Refgem.shp").resolve())
        lm = LayerMapping(Municipality, shapefile_path, municipality_mapping, transform=False, encoding="iso-8859-1")
        lm.save(strict=True, verbose=True)
