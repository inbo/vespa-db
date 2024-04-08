"""."""
from django.contrib.gis.geos import Point

def get_province_from_coordinates(longitude: float, latitude: float): # type: ignore[no-untyped-def]
    """
    Get the province for a given long and lat.

    Parameters
    ----------
    - longitude (float): The longitude coordinate.
    - latitude (float): The latitude coordinate.

    Returns
    -------
    - The province if found, otherwise None.
    """
    from vespadb.observations.models import Province
    point_to_check = Point(longitude, latitude, srid=4326)
    point_to_check.transform(31370)
    province_containing_point = Province.objects.filter(polygon__contains=point_to_check)
    province: 'Province' | None = province_containing_point.first()
    return province