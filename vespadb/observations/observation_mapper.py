"""External API to Observation model mapper functions."""

import logging
from datetime import datetime
from typing import Any

import pytz
from django.contrib.gis.geos import Point

from vespadb.observations.utils import check_if_point_in_anb_area, get_municipality_from_coordinates

logger = logging.getLogger(__name__)


def map_external_data_to_observation_model(external_data: dict[str, Any]) -> dict[str, Any] | None:
    """
    Map external API data to a Django observation model fields, returning None if the data is incomplete or improperly formatted.

    :param external_data: A dictionary of external API data.
    :return: A dictionary suitable for creating or updating an Observation model instance, or None if an error occurs.
    """
    # TODO: add mapping for attributes
    required_fields = ["id", "date", "point", "created", "modified", "species"]
    for field in required_fields:
        if field not in external_data or external_data[field] is None:
            logger.exception(
                "Missing required field: %s in observation external ID {external_data.get('id', 'Unknown')}", field
            )
            return None

    # Handle 'time' being None or missing
    observation_time = external_data.get("time", "00:00:00")

    try:
        # Concatenate date and time to form a full datetime string
        observation_datetime_str = f"{external_data['date']}T{observation_time}"
        # Assume the datetime is in CET and convert to UTC
        cet_timezone = pytz.timezone("Europe/Paris")  # CET timezone
        observation_datetime = datetime.strptime(observation_datetime_str, "%Y-%m-%dT%H:%M:%S").replace(
            tzinfo=cet_timezone
        )
        observation_datetime_utc = observation_datetime.astimezone(pytz.utc)
    except ValueError as e:
        logger.exception(
            f"Invalid date/time format for observation external ID {external_data.get('id', 'Unknown')}: {e}"
        )
        return None

    try:
        # Convert creation and modification datetime from ISO format
        created_datetime = (
            datetime.fromisoformat(external_data["created"]).replace(tzinfo=cet_timezone).astimezone(pytz.utc)
        )
        modified_datetime = (
            datetime.fromisoformat(external_data["modified"]).replace(tzinfo=cet_timezone).astimezone(pytz.utc)
        )
    except ValueError as e:
        logger.exception(f"Invalid ISO date format for external ID {external_data.get('id', 'Unknown')}: {e}")
        return None

    location = Point(external_data["point"]["coordinates"], srid=4326)

    if location:
        long, lat = location.x, location.y
        anb = check_if_point_in_anb_area(long, lat)
        municipality = get_municipality_from_coordinates(long, lat)

    mapped_data = {
        "wn_id": external_data["id"],
        "location": location,
        "source": external_data.get("source", "Unknown"),
        "species": external_data.get("species", 0),
        "observation_datetime": observation_datetime_utc,
        "wn_created_datetime": created_datetime,
        "wn_modified_datetime": modified_datetime,
        "wn_notes": external_data.get("notes", ""),
        "wn_admin_notes": external_data.get("admin_notes", ""),
        "images": external_data.get("photos", []),
        "anb": anb,
        "municipality": municipality,
        "province": municipality.province if municipality else None,
    }
    return mapped_data
