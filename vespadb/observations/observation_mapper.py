"""External API to Observation model mapper functions."""

import logging
from datetime import datetime
from typing import Any

import pytz
from django.contrib.gis.geos import Point

logger = logging.getLogger(__name__)


def map_external_data_to_observation_model(external_data: dict[str, Any]) -> dict[str, Any] | None:
    """
    Map external API data to a Django observation model fields, returning None if the data is incomplete or improperly formatted.

    :param external_data: A dictionary of external API data.
    :return: A dictionary suitable for creating or updating an Observation model instance, or None if an error occurs.
    """
    # Check for required fields
    required_fields = ["id", "date", "point", "created", "modified", "species"]
    for field in required_fields:
        if field not in external_data or external_data[field] is None or not external_data[field]:
            logger.exception(
                "Missing required field: %s in observation external ID %s", field, external_data.get("id", "Unknown")
            )
            return None

    # Handle 'time' being None
    observation_time = external_data.get("time", "00:00:00") if external_data.get("time") else "00:00:00"

    try:
        # Format the observation datetime
        observation_datetime_str = f"{external_data['date']}T{observation_time}"
        # TODO: verify with observations.org if time is in utc
        observation_datetime = datetime.strptime(observation_datetime_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=pytz.utc)
    except ValueError:
        logger.exception("Invalid date/time format for observation external ID %s", external_data.get("id", "Unknown"))
        return None

    # Mapping external data to model fields
    mapped_data = {
        "wn_id": external_data["id"],
        "location": Point(external_data["point"]["coordinates"], srid=4326),
        "source": external_data.get("source", "Unknown"),
        "species": external_data.get("species", 0),
        "observation_datetime": observation_datetime.astimezone(pytz.timezone("Europe/Brussels")),
        "wn_notes": external_data.get("notes", ""),
        "wn_admin_notes": external_data.get("admin_notes", ""),
        "images": external_data.get("photos", []),
    }

    # Convert creation and modification datetime from ISO format
    for field in ["created", "modified"]:
        try:
            mapped_data[f"wn_{field}_datetime"] = datetime.fromisoformat(external_data[field])
        except ValueError:
            logger.exception(
                "Invalid ISO format in '%s' field for observation external ID %s",
                field,
                external_data.get("id", "Unknown"),
            )
            return None

    return mapped_data
