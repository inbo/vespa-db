"""Serializers for the observations app."""

import logging
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry, Point
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework import serializers
from rest_framework.request import Request

from vespadb.observations.helpers import parse_and_convert_to_cet, parse_and_convert_to_utc
from vespadb.observations.models import Municipality, Observation, Province
from vespadb.observations.utils import get_municipality_from_coordinates
from vespadb.users.models import VespaUser

if TYPE_CHECKING:
    from rest_framework.request import Request

logger = logging.getLogger(__name__)

# Define the fields that public users can read
public_read_fields = [
    "id",
    "created_datetime",
    "modified_datetime",
    "location",
    "source",
    "species",
    "nest_height",
    "nest_size",
    "nest_location",
    "nest_type",
    "observation_datetime",
    "wn_cluster_id",
    "modified_by",
    "created_by",
    "province",
    "eradication_datetime",
    "municipality",
    "province",
    "images",
    "public_domain",
    "municipality_name",
    "visible",
    "reserved_by_first_name",
    "modified_by_first_name",
    "created_by_first_name",
]

# Define the fields that authenticated users can read
user_read_fields = [
    "id",
    "wn_id",
    "created_datetime",
    "modified_datetime",
    "location",
    "source",
    "wn_notes",
    "wn_admin_notes",
    "species",
    "nest_height",
    "nest_size",
    "nest_location",
    "nest_type",
    "observation_datetime",
    "notes",
    "modified_by",
    "created_by",
    "wn_modified_datetime",
    "wn_created_datetime",
    "images",
    "reserved_by",
    "reserved_datetime",
    "eradication_datetime",
    "eradicator_name",
    "eradication_duration",
    "eradication_persons",
    "eradication_result",
    "eradication_product",
    "eradication_method",
    "eradication_aftercare",
    "eradication_problems",
    "eradication_notes",
    "municipality",
    "province",
    "anb",
    "public_domain",
    "municipality_name",
    "visible",
    "reserved_by_first_name",
    "modified_by_first_name",
    "created_by_first_name",
]

# Define the conditional fields for authenticated users with specific permissions
conditional_fields = [
    "observer_phone_number",
    "observer_email",
    "observer_name",
]


# Observation serializersclass ObservationSerializer(serializers.ModelSerializer):
class ObservationSerializer(serializers.ModelSerializer):
    """Serializer for the full details of an Observation model instance."""

    municipality_name = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    reserved_by_first_name = serializers.SerializerMethodField()
    modified_by_first_name = serializers.SerializerMethodField()
    created_by_first_name = serializers.SerializerMethodField()

    class Meta:
        """Meta class for the ObservationSerializer."""

        model = Observation
        fields = "__all__"
        extra_kwargs = {
            "wn_id": {"required": False, "allow_null": True},
            "wn_cluster_id": {"required": False, "allow_null": True},
            "eradication_datetime": {"required": False, "allow_null": True},
            "id": {"read_only": True},
            "admin_notes": {"required": False, "allow_blank": True, "allow_null": True},
            "observer_received_email": {"required": False, "allow_null": True},
            "images": {"required": False, "allow_null": True},
            "reserved_by": {"required": False, "allow_null": True},
        }

    def get_municipality_name(self, obj: Observation) -> str | None:
        """Retrieve the name of the municipality associated with the observation, if any."""
        return obj.municipality.name if obj.municipality else None

    def get_status(self, obj: Observation) -> str:
        """Determine the status of the observation based on its properties."""
        if obj.eradication_datetime:
            return "eradicated"
        if obj.reserved_datetime:
            return "reserved"
        return "default"

    def get_reserved_by_first_name(self, obj: Observation) -> str | None:
        """Retrieve the first name of the user who reserved the observation."""
        return obj.reserved_by.first_name if obj.reserved_by else None

    def get_modified_by_first_name(self, obj: Observation) -> str | None:
        """Retrieve the first name of the user who modified the observation."""
        return obj.modified_by.first_name if obj.modified_by else None

    def get_created_by_first_name(self, obj: Observation) -> str | None:
        """Retrieve the first name of the user who created the observation."""
        return obj.created_by.first_name if obj.created_by else None

    def to_representation(self, instance: Observation) -> dict[str, Any]:
        """
        Dynamically filter fields based on user authentication status.

        :param instance: Observation instance.
        :return: A dictionary representation of the observation instance with filtered fields.
        """
        if not instance.municipality and instance.location:
            long = instance.location.x
            lat = instance.location.y
            instance.municipality = get_municipality_from_coordinates(long, lat)
            if instance.municipality:
                instance.province = instance.municipality.province
            instance.save(update_fields=["municipality", "province"])

        data: dict[str, Any] = super().to_representation(instance)
        # Convert datetime fields to CET for outgoing representation
        datetime_fields = [
            "created_datetime",
            "modified_datetime",
            "wn_modified_datetime",
            "wn_created_datetime",
            "reserved_datetime",
            "observation_datetime",
            "eradication_datetime",
        ]
        for field in datetime_fields:
            if data.get(field):
                data[field] = parse_and_convert_to_cet(data[field]).isoformat()

        request: Request = self.context.get("request")
        data["municipality_name"] = self.get_municipality_name(instance)
        if request and request.user.is_authenticated:
            if not request.user.is_staff:
                # Filter fields for non-staff users based on their permissions
                user: VespaUser = request.user
                user_municipality_ids = user.municipalities.values_list("id", flat=True)
                if (
                    user.personal_data_access
                    and instance.municipality
                    and instance.municipality.id in user_municipality_ids
                ):
                    fields_to_include = set(user_read_fields + conditional_fields)
                else:
                    fields_to_include = set(user_read_fields)
                # Filter the data to include only the permitted fields
                filtered_data = {field: data[field] for field in fields_to_include if field in data}
                return filtered_data
            # If user is staff, return all fields as is, no need to modify `data`
            return data
        # For unauthenticated or public access, restrict to public_read_fields
        return {field: data[field] for field in public_read_fields if field in data}

    def validate_reserved_by(self, value: VespaUser) -> VespaUser:
        """Validate that the user does not exceed the maximum number of allowed reservations."""
        if value:
            current_reservations_count = Observation.objects.filter(
                reserved_by=value, eradication_datetime__isnull=True
            ).count()
            if current_reservations_count >= settings.MAX_RESERVATIONS:
                logger.error(f"User {value.id} exceeded the reservation limit.")
                raise ValidationError(
                    f"This user has already reached the maximum number of reservations ({settings.MAX_RESERVATIONS})."
                )
        return value

    def update(self, instance: Observation, validated_data: dict[Any, Any]) -> Observation:
        """Update method to handle observation reservations."""
        user = self.context["request"].user
        if not user.is_staff:
            # Non-admins cannot update admin_notes and observer_received_email fields
            validated_data.pop("admin_notes", None)
            validated_data.pop("observer_received_email", None)

        # Conditionally set `reserved_by` and `reserved_datetime` for all users
        if "reserved_by" in validated_data and instance.reserved_by is None:
            validated_data["reserved_datetime"] = timezone.now() if validated_data["reserved_by"] else None
            instance.reserved_by = user

        # Prevent non-admin users from updating observations reserved by others
        if not user.is_staff and instance.reserved_by and instance.reserved_by != user:
            raise serializers.ValidationError("You cannot edit an observation reserved by another user.")

        # Allow admins to update all fields
        if user.is_staff:
            instance = super().update(instance, validated_data)
            return instance

        # For regular users, restrict the set of fields they can update
        allowed_fields = [
            "nest_height",
            "nest_size",
            "nest_location",
            "nest_type",
            "notes",
            "modified_by",
            "created_by",
            "reserved_by",
            "eradication_datetime",
            "eradicator_name",
            "eradication_result",
            "eradication_product",
            "eradication_notes",
            "images",
        ]

        for field in set(validated_data) - set(allowed_fields):
            validated_data.pop(field)

        instance = super().update(instance, validated_data)
        return instance

    def to_internal_value(self, data: dict[str, Any]) -> dict[str, Any]:
        """Convert the incoming data to a Python native representation."""
        logger.info("Raw input data: %s", data)
        internal_data = super().to_internal_value(data)
        logger.info("Internal data after conversion: %s", internal_data)

        datetime_fields = [
            "created_datetime",
            "modified_datetime",
            "wn_modified_datetime",
            "wn_created_datetime",
            "reserved_datetime",
            "observation_datetime",
            "eradication_datetime",
        ]
        for field in datetime_fields:
            if data.get(field):
                if isinstance(data[field], str):
                    try:
                        internal_data[field] = parse_and_convert_to_utc(data[field])
                    except (ValueError, TypeError) as err:
                        raise serializers.ValidationError({
                            field: [f"Invalid datetime format for {field}."]
                        }).with_traceback(err.__traceback__) from None
                else:
                    internal_data[field] = data[field]

        if "location" in data:
            internal_data["location"] = self.validate_location(data["location"])

        logger.info("Internal data after datetime conversion: %s", internal_data)
        return dict(internal_data)

    def validate_location(self, value: Any) -> Point:
        """Validate the input location data. Handle different formats of location data."""
        if isinstance(value, str):
            try:
                return GEOSGeometry(value, srid=4326)
            except (ValueError, TypeError) as e:
                raise serializers.ValidationError("Invalid WKT format for location.") from e
        elif isinstance(value, dict):
            latitude = value.get("latitude")
            longitude = value.get("longitude")
            if latitude is None or longitude is None:
                raise serializers.ValidationError("Missing or invalid location data")
            return Point(float(longitude), float(latitude), srid=4326)
        raise serializers.ValidationError("Invalid location data type")


# Municipality serializers
class MunicipalitySerializer(serializers.ModelSerializer):
    """Serializer for the Municipality model."""

    class Meta:
        """Meta class for the MunicipalitySerializer."""

        model = Municipality
        fields = ["id", "name"]


class ProvinceSerializer(serializers.ModelSerializer):
    """Serializer for the Province model."""

    class Meta:
        """Meta class for the ProvinceSerializer."""

        model = Province
        fields = ["id", "name"]
