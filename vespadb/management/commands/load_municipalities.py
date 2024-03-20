"""Handle the load_municipalities command."""
from django.core.management.base import BaseCommand
import geopandas as gpd
from vespadb.observations.models import Municipality
import os
from typing import Any
from django.contrib.gis.geos import MultiPolygon, GEOSGeometry, Polygon

class Command(BaseCommand):
    help = 'Load municipalities from a Shapefile into the database'

    def handle(self, *args: Any, **kwargs: Any) -> None:
        """
        Load the municipalities from the Shapefile into the database.

        Args:
            *args (Any): Variable length argument list.
            **kwargs (Any): Arbitrary keyword arguments.

        Returns:
            None
        """
        # Load the GeoDataFrame from the Shapefile
        script_dir = os.path.dirname(os.path.abspath(__file__))
        shp_path = os.path.join(script_dir, 'data/Refgem.shp')

        gdf = gpd.read_file(shp_path)
        for index, row in gdf.iterrows():
            nis_code = row['NISCODE']
            name = row['NAAM']
            geometry = GEOSGeometry(row['geometry'].wkt)
            
            if isinstance(geometry, Polygon):
                geometry = MultiPolygon(geometry)

            municipality, created = Municipality.objects.get_or_create(
                name=name, nis_code=nis_code, defaults={'polygon': geometry}
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'Municipality "{name}" successfully saved.'))
            else:
                # Update the polygon geometry if the municipality exists
                municipality.polygon = geometry
                municipality.save()
                self.stdout.write(self.style.SUCCESS(f'Municipality "{name}" updated.'))
