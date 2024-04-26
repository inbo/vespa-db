"""External API to Observation model mapper functions."""

import logging
from datetime import datetime
from difflib import get_close_matches
from typing import Any, cast

import pytz
from django.contrib.gis.geos import Point
from django.db.models import TextChoices

from vespadb.observations.models import (
    EradicationMethodEnum,
    EradicationProblemsEnum,
    EradicationProductEnum,
    EradicationResultEnum,
    NestHeightEnum,
    NestLocationEnum,
    NestSizeEnum,
    NestTypeEnum,
    ValidationStatusEnum,
)
from vespadb.observations.utils import check_if_point_in_anb_area, get_municipality_from_coordinates

logger = logging.getLogger(__name__)
ENUMS_MAPPING = {
    "Nesthoogte": NestHeightEnum,
    "Nestgrootte": NestSizeEnum,
    "Nestplaats": NestLocationEnum,
    "Nesttype": NestTypeEnum,
    "Resultaat": EradicationResultEnum,
    "Problemen": EradicationProblemsEnum,
    "Methode": EradicationMethodEnum,
    "Product": EradicationProductEnum,
}


def map_attribute_to_enum(value: str, enum: type[TextChoices]) -> TextChoices | None:
    """
    Map a single attribute value to an enum using close match.

    Parameters
    ----------
    - value (str): The value from the API that needs to be mapped to an enum.
    - enum (Type[TextChoices]): The enum type that the value is expected to map to.

    Returns
    -------
    - Optional[TextChoices]: The corresponding enum value if a match is found, otherwise None.
    """
    enum_dict = {e.value: e for e in enum}
    closest_match = get_close_matches(value, enum_dict.keys(), n=1, cutoff=0.6)
    return enum_dict.get(closest_match[0]) if closest_match else None


def map_attributes_to_enums(api_attributes: list[dict[str, str]]) -> dict[str, TextChoices]:
    """
    Map API attributes to model enums based on configured mappings.

    Parameters
    ----------
    - api_attributes (List[Dict[str, Any]]): A list of dictionaries, each containing attribute details from the API.
    - enums_mapping (Dict[str, Type[TextChoices]]): A dictionary mapping attribute names to the Django model enums.

    Returns
    -------
    - Dict[str, TextChoices]: A dictionary containing the attribute names and their mapped enum values.
    """
    mapped_values = {}
    for attribute_dict in api_attributes:
        attr_name = attribute_dict.get("name")
        value = str(attribute_dict.get("value"))
        if attr_name in ENUMS_MAPPING:
            mapped_enum = map_attribute_to_enum(value, ENUMS_MAPPING[attr_name])
            if mapped_enum:
                mapped_values[attr_name] = mapped_enum
            else:
                logger.warning(f"No enum match found for {attr_name}: {value}")
    return mapped_values


def map_validation_status_to_enum(validation_status: str) -> ValidationStatusEnum | None:
    """
    Map a single validation status to an enum.

    Parameters
    ----------
    - validation_status (str): The validation status from the API that needs to be mapped to an enum.

    Returns
    -------
    - ValidationStatusEnum: The corresponding enum value if a match is found, otherwise None.
    """
    validation_status_dict = {
        "O": ValidationStatusEnum.UNKNOWN,
        "J": ValidationStatusEnum.APPROVED_WITH_EVIDENCE,
        "P": ValidationStatusEnum.APPROVED_BY_ADMIN,
        "A": ValidationStatusEnum.APPROVED_AUTOMATIC_VALIDATION,
        "I": ValidationStatusEnum.IN_PROGRESS,
        "N": ValidationStatusEnum.REJECTED,
        "U": ValidationStatusEnum.NOT_EVALUABLE_YET,
    }
    return cast(ValidationStatusEnum, validation_status_dict.get(validation_status))


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
    if observation_time is None:
        observation_time = "00:00:00"

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

    api_attributes = external_data.get("attributes", {})
    mapped_enums = map_attributes_to_enums(api_attributes)
    user = external_data.get("user", {})

    mapped_data = {
        "wn_id": external_data["id"],
        "location": location,
        "source": external_data.get("source"),
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
        "wn_cluster_id": external_data.get("nest"),
        "wn_validation_status": map_validation_status_to_enum(external_data.get("validation_status", "O")),
        "observer_phone_number": user.get("phone_number"),  # TODO; check if this is correct
        "observer_email": user.get("email"),
        "observer_name": user.get("name"),
        **mapped_enums,
    }
    return mapped_data
