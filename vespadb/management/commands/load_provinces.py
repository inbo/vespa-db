"""Handlers."""

from pathlib import Path
from typing import Any

from django.contrib.gis.utils import LayerMapping
from django.core.management.base import BaseCommand

from vespadb.observations.models import Province

provinces_mapping = {
    "oidn": "OIDN",
    "uidn": "UIDN",
    "terrid": "TERRID",
    "nis_code": "NISCODE",
    "name": "NAAM",
    "length": "LENGTE",
    "surface": "OPPERVL",
    "polygon": "GEOMETRY",
}

class Command(BaseCommand):
    """A custom management command that loads a ShapeFile containing province boundaries into the database.

    This command uses the LayerMapping utility from Django's GIS framework to perform the data import.
    """

    help: str = "Laadt een ShapeFile met provinciegrenzen in de database."

    def handle(self, *args: Any, **options: Any) -> None:
        """
        Handle province data loading.

        :param args: Variable length argument list.
        :param options: Arbitrary keyword arguments.
        """
        shapefile_path: str = str((Path(__file__).parent / "data" / "provinces" / "Refprv.shp").resolve())

        lm = LayerMapping(Province, shapefile_path, provinces_mapping, transform=False, encoding="iso-8859-1")
        lm.save(strict=True, verbose=True)