"""."""

import logging
from enum import Enum
from typing import TYPE_CHECKING, Any

from django.contrib.auth.models import AbstractUser
from django.contrib.gis.geos import Point
from django.db import models
from geopy.geocoders import Nominatim

from vespadb.observations.models import Province
from vespadb.helpers import get_province_from_coordinates

if TYPE_CHECKING:
    from geopy.location import Location
logger = logging.getLogger(__name__)


class UserType(Enum):
    """User Type Enum."""

    ADMIN = "admin"
    REGULAR = "regular"
    SYNC = "sync"
    IMPORT = "import"

    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        """Return choices for the enum."""
        return [(key.value, key.name) for key in cls]


def get_coordinates_from_postal_code(postal_code: str, country: str = "Belgium") -> tuple[float, float]:
    """
    Return the latitude and longitude coordinates for a given postal code in Belgium.

    Parameters
    ----------
    - postal_code (str): The postal code for which to find the coordinates.
    - country (str): The country where the postal code is located. Default is "Belgium".

    Returns
    -------
    - A tuple (latitude, longitude) if coordinates are found, otherwise None.

    Example usage:
    >>> get_coordinates_from_postal_code("1000")
    (50.8465573, 4.351697)

    Note:
    This function uses the Nominatim geocoding service. Ensure compliance with Nominatim's usage policy.
    """
    geolocator = Nominatim(user_agent="get_coordinates_app")
    location: Location = geolocator.geocode(f"{postal_code}, {country}")

    if location:
        return location.latitude, location.longitude
    raise ValueError("Postal code is invalid.")

class VespaUser(AbstractUser):
    """Model for the Vespa user."""

    user_type = models.CharField(
        max_length=10,
        choices=UserType.choices(),
        default=UserType.REGULAR.value,
    )
    personal_data_access = models.BooleanField(default=False)
    postal_code = models.CharField(max_length=12, null=True, blank=True)
    province = models.ForeignKey(
        Province,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Override the save method to automatically assign a municipality based on the observation's location.

        :param args: Variable length argument list.
        :param kwargs: Arbitrary keyword arguments.
        """
        # Only compute the municipality if the location is set and the municipality is not
        if self.postal_code:
            lat, long = get_coordinates_from_postal_code(postal_code=self.postal_code)
            self.province = get_province_from_coordinates(long, lat)

        super().save(*args, **kwargs)
