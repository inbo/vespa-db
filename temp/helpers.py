"""Helper functions for generating random points inside or outside a municipality polygon."""
from typing import Tuple, Optional
import geopandas as gpd
from shapely.geometry import MultiPolygon, Point
from pathlib import Path
import random
from pyproj import Transformer
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon

def get_random_municipality() -> Tuple[Optional[str], Optional[str], Optional[MultiPolygon]]:
    """
    Selects a random municipality from a shapefile.

    Returns:
        Tuple[Optional[str], Optional[str], Optional[MultiPolygon]]: A tuple containing the name,
        NIS code of the municipality, and its polygon geometry. Returns None for each if the
        municipality cannot be selected.
    """
    try:
        script_dir = Path(__file__).resolve().parent
        shp_path = script_dir / "data/Refgem.shp"
        gdf = gpd.read_file(str(shp_path))

        if gdf.empty:
            return None, None, None

        municipality_row = gdf.sample(1).iloc[0]
        name = municipality_row['NAAM']
        nis_code = municipality_row['NISCODE']
        geometry = municipality_row.geometry

        if not isinstance(geometry, MultiPolygon):
            geometry = MultiPolygon([geometry])

        return name, nis_code, geometry

    except Exception as e:
        print(f"An error occurred: {e}")
        return None, None, None


def get_point_from_municipality(polygon: MultiPolygon) -> Optional[Point]:
    """
    Generates a random point inside or outside the given municipality polygon.

    Args:
        polygon (MultiPolygon): The polygon of the municipality.
        inside (bool): If True, generates a point inside the polygon. If False, outside.

    Returns:
        Optional[Point]: A Shapely Point object either inside or outside the polygon.
                         Returns None if a point cannot be generated.
    """
    minx, miny, maxx, maxy = polygon.bounds
    while True:
        point = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
        if polygon.contains(point):
            return point
            
def convert_to_lat_lon(x: float, y: float) -> Tuple[float, float]:
    """
    Converts projected coordinates to latitude and longitude.
    """
    transformer = Transformer.from_crs("epsg:31370", "epsg:4326", always_xy=True)
    lon, lat = transformer.transform(x, y)
    return lat, lon


def get_municipality_by_coordinates(lat: float, lon: float, gdf: gpd.GeoDataFrame) -> Optional[str]:
    """
    Finds and returns the name of the municipality containing the given latitude and longitude.
    Requires a GeoDataFrame of municipalities to search within.

    Args:
        lat (float): The latitude.
        lon (float): The longitude.
        gdf (gpd.GeoDataFrame): The GeoDataFrame containing municipality data.

    Returns:
        Optional[str]: The name of the municipality, or None if not found.
    """
    point = Point(lon, lat)
    for _, row in gdf.iterrows():
        if row.geometry.contains(point):
            return str(row['NAAM'])
    return None
