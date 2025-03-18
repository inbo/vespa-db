"""
Usage: python manage.py list_near_anb --lon 3.838 --lat 51.0997 --max-distance 10000
"""
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from vespadb.observations.models import ANB

class Command(BaseCommand):
    help = 'List all ANB areas near a given point with distance and detailed info'

    def add_arguments(self, parser):
        parser.add_argument(
            '--lon',
            type=float,
            default=3.838,
            help='Longitude of the point (in EPSG:4326). Default: 3.838'
        )
        parser.add_argument(
            '--lat',
            type=float,
            default=51.0997,
            help='Latitude of the point (in EPSG:4326). Default: 51.0997'
        )
        parser.add_argument(
            '--max-distance',
            type=float,
            default=10000,
            help='Maximum distance in meters to filter ANB areas. Default: 10000 m'
        )

    def handle(self, *args, **options):
        lon = options['lon']
        lat = options['lat']
        max_distance = options['max_distance']
        
        self.stdout.write(f"Searching ANB areas near point ({lon}, {lat}) within {max_distance} meters...\n")
        
        # Create the point in WGS84 (EPSG:4326)
        pt = Point(lon, lat, srid=4326)
        # Transform the point to the same SRID as the ANB polygons (31370)
        pt.transform(31370)
        
        # Annotate each ANB area with its distance to the point and order by distance
        anb_areas = ANB.objects.annotate(distance=Distance('polygon', pt)).order_by('distance')
        
        found = False
        for anb in anb_areas:
            distance_m = anb.distance.m  # Distance in meters
            if distance_m <= max_distance:
                self.stdout.write(
                    f"ID: {anb.id}, Domain: {anb.domain}, Province: {anb.province}, "
                    f"Distance: {distance_m:.2f} m"
                )
                found = True
        
        if not found:
            self.stdout.write("No ANB areas found within the specified distance.")
