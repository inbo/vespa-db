"""Utility functions for the observations app."""

from django.contrib.gis.geos import Point
import time
from functools import wraps
from django.db import connection, OperationalError
from typing import Callable, TypeVar, Any, cast, Generator, List

F = TypeVar("F", bound=Callable[..., Any])

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

def db_retry(retries: int = 3, delay: int = 5) -> Callable[[F], F]:
    """
    Decorator to retry a database operation in case of an OperationalError.

    Args:
        retries (int): Number of retry attempts. Defaults to 3.
        delay (int): Delay between retries in seconds. Defaults to 5.

    Returns:
        Callable: The wrapped function with retry logic.
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except OperationalError:
                    if attempt < retries - 1:
                        time.sleep(delay)
                        connection.close()
                    else:
                        raise
        return cast(F, wrapper)
    return decorator

def retry_query(queryset: Generator[Any, None, None], retries: int = 3, delay: int = 5) -> List[Any]:
    """Execute a query with retries to handle intermittent database connection errors."""
    for attempt in range(retries):
        try:
            return list(queryset)
        except OperationalError:
            if attempt < retries - 1:
                time.sleep(delay)
                connection.close()
            else:
                # Raise a more informative error if retries are exhausted
                raise OperationalError(f"Database connection failed after {retries} attempts")
    
    # This return is added to satisfy type checkers, though it should never reach here.
    return []
