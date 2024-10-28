"""External API to Observation model mapper functions."""

import logging
from datetime import datetime
from difflib import get_close_matches
from typing import Any, cast

import pytz
from django.conf import settings
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
    Observation,
    ValidationStatusEnum,
)
from vespadb.observations.utils import check_if_point_in_anb_area, get_municipality_from_coordinates

logger = logging.getLogger("vespadb.observations.tasks")

ENUMS_MAPPING: dict[str, type[TextChoices]] = {
    "Nesthoogte": NestHeightEnum,
    "Nestgrootte": NestSizeEnum,
    "Nestplaats": NestLocationEnum,
    "Nesttype": NestTypeEnum,
    "Resultaat": EradicationResultEnum,
    "Problemen": EradicationProblemsEnum,
    "Methode": EradicationMethodEnum,
    "Product": EradicationProductEnum,
}
ENUM_FIELD_MAPPING: dict[str, str] = {
    "Nesthoogte": "nest_height",
    "Nestgrootte": "nest_size",
    "Nestplaats": "nest_location",
    "Nesttype": "nest_type",
    "Resultaat": "eradication_result",
    "Problemen": "eradication_problems",
    "Methode": "eradication_method",
    "Product": "eradication_product",
}


def map_attribute_to_enum(value: str, enum: type[TextChoices]) -> TextChoices | None:
    """
    Map a single attribute value to an enum using close match.

    :param value: The value from the API that needs to be mapped to an enum.
    :param enum: The enum type that the value is expected to map to.
    :return: The corresponding enum value if a match is found, otherwise None.
    """
    enum_dict = {e.value: e for e in enum}
    closest_match = get_close_matches(value, enum_dict.keys(), n=1, cutoff=0.6)
    return enum_dict.get(closest_match[0]) if closest_match else None


def map_attributes_to_enums(api_attributes: list[dict[str, str]]) -> dict[str, TextChoices]:
    """
    Map API attributes to model enums based on configured mappings.

    :param api_attributes: A list of dictionaries, each containing attribute details from the API.
    :return: A dictionary containing the attribute names and their mapped enum values.
    """
    mapped_values = {}
    for attribute in api_attributes:
        attr_name = attribute.get("name")
        value = str(attribute.get("value"))
        if attr_name in ENUMS_MAPPING:
            mapped_enum = map_attribute_to_enum(value, ENUMS_MAPPING[attr_name])
            if mapped_enum:
                mapped_values[ENUM_FIELD_MAPPING[attr_name]] = mapped_enum
            else:
                logger.warning(f"No enum match found for {attr_name}: {value}")
    return mapped_values


def map_validation_status_to_enum(validation_status: str) -> ValidationStatusEnum | None:
    """
    Map a single validation status to an enum.

    :param validation_status: The validation status from the API that needs to be mapped to an enum.
    :return: The corresponding enum value if a match is found, otherwise None.
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


def parse_datetime_with_timezone(
    date_str: str, time_str: str = "00:00:00", timezone_str: str = "Europe/Paris"
) -> datetime:
    """
    Parse a datetime string with timezone into a datetime object in UTC.

    :param date_str: Date string in format "%Y-%m-%d".
    :param time_str: Time string in format "%H:%M:%S", default is "00:00:00".
    :param timezone_str: Timezone string, default is "Europe/Paris" (CET).
    :return: Datetime object converted to UTC.
    :raises ValueError: If the input format is incorrect.
    """
    timezone = pytz.timezone(timezone_str)
    datetime_str = f"{date_str}T{time_str}"
    datetime_obj = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone)
    return datetime_obj.astimezone(pytz.utc)


def map_external_data_to_observation_model(external_data: dict[str, Any]) -> dict[str, Any] | None:  # noqa: C901
    """
    Map external API data to a Django observation model fields, returning None if the data is incomplete or improperly formatted.

    :param external_data: A dictionary of external API data.
    :return: A dictionary suitable for creating or updating an Observation model instance, or None if an error occurs.
    """
    required_fields = ["id", "date", "point", "created", "modified", "species"]
    for field in required_fields:
        if field not in external_data or external_data[field] is None:
            logger.error(
                f"Missing required field: {field} in observation external ID {external_data.get('id', 'Unknown')}"
            )
            return None

    try:
        observation_time = external_data.get("time", "00:00:00")
        if observation_time is None:
            observation_time = "00:00:00"
        observation_datetime_utc = parse_datetime_with_timezone(external_data["date"], observation_time)

        created_datetime = (
            datetime.fromisoformat(external_data["created"])
            .replace(tzinfo=pytz.timezone("Europe/Paris"))
            .astimezone(pytz.utc)
        )
        modified_datetime = (
            datetime.fromisoformat(external_data["modified"])
            .replace(tzinfo=pytz.timezone("Europe/Paris"))
            .astimezone(pytz.utc)
        )
    except ValueError as e:
        logger.exception(f"Invalid date/time or ISO format: {e} for external ID {external_data.get('id', 'Unknown')}")
        return None

    location = Point(external_data["point"]["coordinates"], srid=4326)
    long, lat = location.x, location.y
    anb = check_if_point_in_anb_area(long, lat)
    municipality = get_municipality_from_coordinates(long, lat)

    mapped_enums = map_attributes_to_enums(external_data.get("attributes", []))
    validation_status = map_validation_status_to_enum(external_data.get("validation_status", "O"))

    nest = external_data.get("nest", {})
    cluster_id = None
    if nest:
        cluster_id = nest.get("id")
    mapped_data = {
        "wn_id": external_data["id"],
        "location": location,
        "species": external_data.get("species"),
        "observation_datetime": observation_datetime_utc,
        "wn_created_datetime": created_datetime,
        "wn_modified_datetime": modified_datetime,
        "anb": anb,
        "municipality": municipality,
        "province": municipality.province if municipality else None,
        "wn_validation_status": validation_status,
        "wn_cluster_id": cluster_id,
        "images": external_data.get("photos", []),
        "source": "Waarnemingen.be",
        **mapped_enums,
    }

    # Additional user data
    user_data = external_data.get("user", {})
    if user_data:
        mapped_data.update({
            "observer_phone_number": user_data.get("phone_number"),
            "observer_email": user_data.get("email"),
            "observer_name": user_data.get("name"),
        })

    # Eradication specifics
    eradication_flagged = False

    # Check for eradication keywords in notes
    if (
        "notes" in external_data
        and external_data["notes"]
        and any(keyword in external_data["notes"].upper() for keyword in settings.ERADICATION_KEYWORD_LIST)
        and not check_existing_eradication_date(external_data["id"])
    ):
        eradication_flagged = True

    # Check for "BESTREDEN" in 'Remark (Asian hornet)' attribute
    for attribute in external_data.get("attributes", []):
        if attribute.get("name") == "Remark (Asian hornet)" and "BESTREDEN" in attribute.get("value", "").upper():
            eradication_flagged = True
            break

    if eradication_flagged and not check_existing_eradication_date(external_data["id"]):
        mapped_data["eradication_date"] = observation_datetime_utc.date()
        mapped_data["eradicator_name"] = "Gemeld als bestreden"

    return mapped_data


def check_existing_eradication_date(wn_id: str) -> bool:
    """
    Check if the eradication_date is already set for the given wn_id.

    :param wn_id: The ID of the observation from the external API.
    :return: True if the eradication_date is already set, False otherwise.
    """
    try:
        observation = Observation.objects.get(wn_id=wn_id)
        return observation.eradication_date is not None
    except Observation.DoesNotExist:
        return False
