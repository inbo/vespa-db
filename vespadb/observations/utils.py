"""Utility functions for the observations app."""

from django.contrib.gis.geos import Point


def get_municipality_from_coordinates(longitude: float, latitude: float):  # type: ignore[no-untyped-def]
    """Get the municipality for a given long and lat."""
    from vespadb.observations.models import Municipality  # noqa: PLC0415

    point_to_check = Point(longitude, latitude, srid=4326)
    point_to_check.transform(31370)

    municipalities_containing_point = Municipality.objects.filter(polygon__contains=point_to_check)
    municipality: Municipality | None = municipalities_containing_point.first()
    return municipality


def check_if_point_in_anb_area(longitude: float, latitude: float) -> bool:
    """Check if a given point is in an ANB area."""
    from vespadb.observations.models import ANB  # noqa: PLC0415

    point_to_check = Point(longitude, latitude, srid=4326)
    point_to_check.transform(31370)

    anb_areas_containing_point = ANB.objects.filter(polygon__contains=point_to_check)
    return bool(anb_areas_containing_point)
