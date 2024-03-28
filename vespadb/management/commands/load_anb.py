"""Handlers."""

from pathlib import Path
from typing import Any

from django.contrib.gis.utils import LayerMapping
from django.core.management.base import BaseCommand

from vespadb.observations.models import ANB
import geopandas as gpd

# A mapping dictionary to map field names from the Shapefile to the ANB model fields.
anb_mapping = {
    "domain": "domeinnaam", 
    "province": "provincie", 
    "regio": "regio", 
    "liberties": "rechtenanb", 
    "administrator": "beheerder",
    "contact": "contact_em", 
    "polygon": "geometry",
}

class Command(BaseCommand):
    """A custom management command that loads a ShapeFile containing anb boundaries into the database.

    This command uses the LayerMapping utility from Django's GIS framework to perform the data import.
    """

    help: str = "Laadt een ShapeFile met gemeentegrenzen in de database."

    def handle(self, *args: Any, **options: Any) -> None:
        """
        Handle anb data loading.

        :param args: Variable length argument list.
        :param options: Arbitrary keyword arguments.
        """
        shapefile_path: str = str((Path(__file__).parent / "data" / "anb" / "am_patdat.shp").resolve())

        lm = LayerMapping(ANB, shapefile_path, anb_mapping, transform=False, encoding="iso-8859-1")
        lm.save(strict=True, verbose=True)