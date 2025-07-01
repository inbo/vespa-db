"""External API to Observation model mapper functions."""

import logging
from datetime import datetime
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

mapping_dict: dict[int, dict[str, str]] = {
    329: {
        # Controlled values
        "hoger_dan_4_meter": "hoger_dan_4_meter",
        "lager_dan_4_meter": "lager_dan_4_meter",
        # others
        "Hoger dan 4 meter": "hoger_dan_4_meter",
        "Higher than 4 meters": "hoger_dan_4_meter",
        "Lager dan 4 meter": "lager_dan_4_meter",
        "Lower than 4 meters": "lager_dan_4_meter",
    },
    330: {
        # Controlled values
        "groter_dan_25_cm": "groter_dan_25_cm",
        "kleiner_dan_25_cm": "kleiner_dan_25_cm",
        # others
        "Groter dan 25 cm": "groter_dan_25_cm",
        "Kleiner dan 25 cm": "kleiner_dan_25_cm",
        "Larger than 25cm": "groter_dan_25_cm",
        "Smaller than 25cm": "kleiner_dan_25_cm",
    },
    331: {
        # Controlled values
        "buiten_onbedekt_op_gebouw": "buiten_onbedekt_op_gebouw",
        "buiten_onbedekt_in_boom_of_struik": "buiten_onbedekt_in_boom_of_struik",
        "buiten_natuurlijk_overdekt": "buiten_natuurlijk_overdekt",
        "buiten_maar_overdekt_door_constructie": "buiten_maar_overdekt_door_constructie",
        "binnen_in_gebouw_of_constructie": "binnen_in_gebouw_of_constructie",
        # others
        "Binnen, in gebouw of constructie": "binnen_in_gebouw_of_constructie",
        "Buiten, maar overdekt door constructie": "buiten_maar_overdekt_door_constructie",
        "Buiten, natuurlijk overdekt": "buiten_natuurlijk_overdekt",
        "Buiten, onbedekt in boom of struik": "buiten_onbedekt_in_boom_of_struik",
        "Buiten, onbedekt op gebouw": "buiten_onbedekt_op_gebouw",
        "Inside, in a building or construction": "binnen_in_gebouw_of_constructie",
        "Outside, but covered by construction": "buiten_maar_overdekt_door_constructie",
        "Outside, natural cover": "buiten_natuurlijk_overdekt",
        "Outside, uncovered in a tree or bush": "buiten_onbedekt_in_boom_of_struik",
        "Outside, uncovered on building": "buiten_onbedekt_op_gebouw",
    },
    368: {
        # Controlled values
        "actief_embryonaal_nest": "actief_embryonaal_nest",
        "actief_primair_nest": "actief_primair_nest",
        "actief_secundair_nest": "actief_secundair_nest",
        "inactief_leeg_nest": "inactief_leeg_nest",
        # others
        "Actief embryonaal nest": "actief_embryonaal_nest",
        "Actief embryonaal nest (van maart tot eind juni, nest met enkel koningin)": "actief_embryonaal_nest",
        "Actief primair nest": "actief_primair_nest",
        "Actief primair nest (van juni tot eind november, nest met werksters op lage hoogte (tot 6 meter))": "actief_primair_nest",
        "Actief secundair nest": "actief_secundair_nest",
        "Actief secundair nest (van augustus tot eind november, nest met werksters op grote hoogte (tot 30m))": "actief_secundair_nest",
        "Active embryonic nest": "actief_embryonaal_nest",
        "Active embryonic nest (from march to the end of june, nest with queen only)": "actief_embryonaal_nest",
        "Active primary nest": "actief_primair_nest",
        "Active primary nest (from june to the end of november, nest with workers at low altitude (up to 6m))": "actief_primair_nest",
        "Active secondary nest": "actief_secundair_nest",
        "Active secondary nest (from aug. to the end of nov., nest with workers at high altitude (up to 30m))": "actief_secundair_nest",
        "Inactief/leeg nest (typisch tijdens wintermaanden, een leeg nest hoog in een boom)": "inactief_leeg_nest",
        "Inactief/leeg nest (typisch tijdens wintermaanden, een leeg netst oog in een boom)": "inactief_leeg_nest",
        "Inactive/empty nest": "inactief_leeg_nest",
        "Inactive/empty nest (typically during the winter months, an empty nest high in a tree)": "inactief_leeg_nest",
        "Potential nest": None,
        "Potentieel nest": None,
        "Potentieel nest (onzeker van de soort)": None,
    },
}

ENUMS_MAPPING: dict[str, type[TextChoices]] = {
    "Nest height": NestHeightEnum,
    "Nest size": NestSizeEnum,
    "Nest location": NestLocationEnum,
    "Nest type": NestTypeEnum,
    "Result": EradicationResultEnum,
    "Problems": EradicationProblemsEnum,
    "Method": EradicationMethodEnum,
    "Product": EradicationProductEnum,
}
ENUM_FIELD_MAPPING: dict[int, str] = {
    329: "nest_height",
    330: "nest_size",
    331: "nest_location",
    368: "nest_type",
}
# Literal mapping functions
def map_nest_height_attribute_to_enum(value: str) -> Any | None:
    """Maps Nest height values to enums based on literal mapping."""
    return mapping_dict[329].get(value.strip())

def map_nest_size_attribute_to_enum(value: str) -> Any | None:
    """Maps Nest size values to enums based on literal mapping."""
    return mapping_dict[330].get(value.strip())

def map_nest_location_attribute_to_enum(value: str) -> str | None:
    """Maps Nest location values to enums based on literal mapping."""
    return mapping_dict[331].get(value.strip())

def map_nest_type_attribute_to_enum(value: str) -> str | None:
    """Maps Nest location values to enums based on literal mapping."""
    return mapping_dict[368].get(value.strip())

def map_attribute_to_enum(attribute_id: int, value: str) -> str | None:
    """
    Maps a single attribute value to an enum using literal mapping functions.
    """
    if attribute_id == 329:
        return map_nest_height_attribute_to_enum(value)
    elif attribute_id == 330:
        return map_nest_size_attribute_to_enum(value)
    elif attribute_id == 331:
        return map_nest_location_attribute_to_enum(value)
    elif attribute_id == 368:
        return map_nest_type_attribute_to_enum(value)
    else:
        return None

def map_attributes_to_enums(api_attributes: list[dict[str, Any]]) -> dict[str, str]:
    """
    Map API attributes to model enums based on configured mappings.

    :param api_attributes: A list of dictionaries, each containing attribute details from the API.
    :return: A dictionary containing the attribute names and their mapped enum values.
    """
    mapped_values = {}
    for attribute in api_attributes:
        attribute_id = int(attribute.get("attribute", 0))
        attr_name = attribute.get("name")
        value = str(attribute.get("value"))
        if attribute_id in mapping_dict:
            mapped_enum = map_attribute_to_enum(attribute_id, value)
            if mapped_enum:
                mapped_values[ENUM_FIELD_MAPPING[attribute_id]] = mapped_enum
            else:
                logger.debug(f"No enum match found for {attr_name}: {value}")
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
    date_str: str, time_str: str = "00:00:00", timezone_str: str | None = None
) -> datetime:
    """
    Parse a datetime string into a UTC datetime object.

    :param date_str: Date string in format "%Y-%m-%d".
    :param time_str: Time string in format "%H:%M:%S", default is "00:00:00".
    :param timezone_str: Timezone string, default is None (assume UTC).
    :return: Datetime object in UTC.
    :raises ValueError: If the input format is incorrect.
    """
    # Combine date and time strings
    datetime_str = f"{date_str}T{time_str}"

    # If timezone_str is provided, use it; otherwise assume CET
    if timezone_str and timezone_str != "Europe/Brussels":
        timezone = pytz.timezone(timezone_str)
        datetime_obj = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone)
        # Convert to CET
        datetime_obj = datetime_obj.astimezone(pytz.timezone("Europe/Brussels"))
    else:
        # Assume CET if no timezone is provided or it's already CET
        datetime_obj = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S")
        datetime_obj = pytz.timezone("Europe/Brussels").localize(datetime_obj)

    # Always return CET
    return datetime_obj


def map_external_data_to_observation_model(external_data: dict[str, Any]) -> dict[str, Any] | None:  # noqa: C901
    """
    Map external API data to a Django observation model fields, returning None if the data is incomplete or improperly formatted.

    :param external_data: A dictionary of external API data.
    :return: A dictionary suitable for creating or updating an Observation model instance, or None if an error occurs.
    """
    required_fields = ["id", "date", "point", "created", "modified"]
    for field in required_fields:
        if field not in external_data or external_data[field] is None:
            logger.error(
                f"Missing required field: {field} in observation external ID {external_data.get('id', 'Unknown')}"
            )
            return None

    try:
        observation_time = external_data.get("time", "00:00:00") or "00:00:00"
        # Parse observation_datetime assuming ETC unless specified otherwise
        observation_datetime_cet = parse_datetime_with_timezone(external_data["date"], observation_time)

        # Parse created and modified datetimes from ISO format, assuming UTC
        cet_tz = pytz.timezone("Europe/Brussels")
        created_datetime = datetime.fromisoformat(external_data["created"].replace("Z", ""))
        created_datetime = created_datetime.replace(tzinfo=pytz.UTC).astimezone(cet_tz)
        modified_datetime = datetime.fromisoformat(external_data["modified"].replace("Z", ""))
        modified_datetime = modified_datetime.replace(tzinfo=pytz.UTC).astimezone(cet_tz)
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
    cluster_id = nest.get("id") if nest else None

    mapped_data = {
        "wn_id": external_data["id"],
        "location": location,
        "observation_datetime": observation_datetime_cet,
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

    user_data = external_data.get("user", {})
    if user_data:
        mapped_data.update({
            "observer_phone_number": user_data.get("phone_number"),
            "observer_email": user_data.get("email"),
            "observer_name": user_data.get("name"),
        })

    eradication_flagged = False
    if (
        "notes" in external_data
        and external_data["notes"]
        and any(keyword in external_data["notes"] for keyword in settings.ERADICATION_KEYWORD_LIST)
        and not check_existing_eradication_date(external_data["id"])
    ):
        eradication_flagged = True

    for attribute in external_data.get("attributes", []):
        if attribute.get("attribute") == 369 and "BESTREDEN" in attribute.get("value", ""):
            eradication_flagged = True
            break

    if eradication_flagged:
        mapped_data["eradication_date"] = observation_datetime_cet.date()
        mapped_data["eradicator_name"] = "Gemeld als bestreden"
        if "eradication_result" not in mapped_data or not mapped_data["eradication_result"]:
            mapped_data["eradication_result"] = "successful" 

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
