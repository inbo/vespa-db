"""Serializers for the observations app."""

import logging
import re
from datetime import UTC, datetime, date
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry, Point
from django.core.exceptions import PermissionDenied, ValidationError
from pytz import timezone
from rest_framework import serializers
from rest_framework.request import Request

from vespadb.observations.helpers import parse_and_convert_to_cet, parse_and_convert_to_utc
from vespadb.observations.models import EradicationResultEnum, Municipality, Observation, Province, Export
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
    "nest_height",
    "nest_size",
    "nest_location",
    "nest_type",
    "observation_datetime",
    "modified_by",
    "created_by",
    "eradication_date",
    "municipality",
    "province",
    "images",
    "public_domain",
    "municipality_name",
    "modified_by_first_name",
    "created_by_first_name",
    "notes",
    "eradication_result",
    "wn_id",
    "wn_validation_status",
    "visible",
]

# Define the fields that authenticated users can read
user_read_fields = [
    "id",
    "wn_id",
    "created_datetime",
    "modified_datetime",
    "location",
    "source",
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
    "wn_validation_status",
    "images",
    "reserved_by",
    "reserved_datetime",
    "eradication_date",
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
    "visible",
]

# Define the conditional fields for authenticated users with specific permissions
conditional_fields = [
    "observer_phone_number",
    "observer_email",
    "observer_name",
]

# Fields that require special permissions (admins or specific user permissions)
admin_or_special_permission_fields = [
    "wn_admin_notes",
]

DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class ObservationSerializer(serializers.ModelSerializer):
    """Serializer for the full details of an Observation model instance."""

    municipality_name = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    reserved_by_first_name = serializers.SerializerMethodField()
    modified_by_first_name = serializers.SerializerMethodField()
    created_by_first_name = serializers.SerializerMethodField()
    eradication_date = serializers.DateField(
        required=False, allow_null=True, format="%Y-%m-%d", input_formats=["%Y-%m-%d"]
    )

    class Meta:
        """Meta class for the ObservationSerializer."""

        model = Observation
        fields = "__all__"
        
    def get_municipality_name(self, obj: Observation) -> str | None:
        """Retrieve the name of the municipality associated with the observation, if any."""
        return obj.municipality.name if obj.municipality else None

    def get_status(self, obj: Observation) -> str:
        """Determine the status of the observation based on its properties."""
        if obj.eradication_result:
            return "eradicated"
        if obj.reserved_by:
            return "reserved"
        return "untreated"

    def get_reserved_by_first_name(self, obj: Observation) -> str | None:
        """Retrieve the first name of the user who reserved the observation."""
        return obj.reserved_by.first_name if obj.reserved_by else None

    def get_modified_by_first_name(self, obj: Observation) -> str | None:
        """Retrieve the first name of the user who modified the observation."""
        return obj.modified_by.first_name if obj.modified_by else None

    def get_created_by_first_name(self, obj: Observation) -> str | None:
        """Retrieve the first name of the user who created the observation."""
        return obj.created_by.first_name if obj.created_by else None
        
    def to_representation(self, instance: Observation) -> dict[str, Any]:  # noqa: C901
        """Dynamically filter fields based on user authentication status."""
        if not instance.municipality and instance.location:
            long = instance.location.x
            lat = instance.location.y
            instance.municipality = get_municipality_from_coordinates(long, lat)
            if instance.municipality:
                instance.province = instance.municipality.province
            instance.save(update_fields=["municipality", "province"])

        data: dict[str, Any] = super().to_representation(instance)
        observation_datetime = data.get('observation_datetime')
        if 'created_by' not in data or data['created_by'] is None:
            data['created_by_first_name'] = None
        
        if isinstance(observation_datetime, date) and not isinstance(observation_datetime, datetime):
            data['observation_datetime'] = datetime.combine(observation_datetime, datetime.min.time())
        
        data.pop("wn_admin_notes", None)
        datetime_fields = [
            "created_datetime",
            "modified_datetime",
            "wn_modified_datetime",
            "wn_created_datetime",
            "reserved_datetime",
            "observation_datetime",
        ]
        date_fields = ["eradication_date"]
        for field in datetime_fields:
            if data.get(field):
                data[field] = parse_and_convert_to_cet(data[field]).isoformat()
        for field in date_fields:
            if data.get(field):
                date_str: str = data[field]
                try:
                    parsed_date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=UTC)
                    data[field] = parsed_date.strftime("%Y-%m-%d")
                except ValueError:
                    parsed_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=UTC)
                    data[field] = parsed_date.strftime("%Y-%m-%d")

        request: Request = self.context.get("request")
        data["municipality_name"] = self.get_municipality_name(instance)

        if request and request.user.is_authenticated:
            user: VespaUser = request.user
            permission_level = user.get_permission_level()
            user_municipality_ids = user.municipalities.values_list("id", flat=True)
            is_inside_user_municipality = (
                instance.municipality and instance.municipality.id in user_municipality_ids
            )

            # Voor gebruikers zonder toegang tot specifieke gemeenten
            if permission_level == "logged_in_without_municipality":
                return {field: data[field] for field in public_read_fields if field in data}

            # Voor gebruikers met toegang tot specifieke gemeenten, extra gegevens tonen indien binnen hun gemeenten
            if is_inside_user_municipality or request.user.is_superuser:
                return {field: data[field] for field in user_read_fields if field in data}

            # Voor observaties buiten de gemeenten van de gebruiker, beperk tot publieke velden
            return {field: data[field] for field in public_read_fields if field in data}

        # Voor niet-ingelogde gebruikers, retourneer enkel de publieke velden
        return {field: data[field] for field in public_read_fields if field in data}

    def validate_reserved_by(self, value: VespaUser) -> VespaUser:
        """Validate that the user does not exceed the maximum number of allowed reservations and has permission to reserve in the specified municipality."""
        if value:
            request = self.context.get("request")

            # Skip validation for admin users
            if request and request.user.is_superuser:
                return value

            current_reservations_count = Observation.objects.filter(
                reserved_by=value, eradication_date__isnull=True
            ).count()
            if current_reservations_count >= settings.MAX_RESERVATIONS:
                raise ValidationError(
                    f"This user has already reached the maximum number of reservations ({settings.MAX_RESERVATIONS})."
                )

            observation_municipality = self.instance.municipality if self.instance else None
            user_municipality_ids = request.user.municipalities.values_list("id", flat=True)
            if observation_municipality and observation_municipality.id not in user_municipality_ids:
                raise ValidationError("You do not have permission to reserve nests in this municipality.")
        return value

    def update(self, instance: Observation, validated_data: dict[Any, Any]) -> Observation:  # noqa: C901
        """Update method to handle observation reservations."""
        user = self.context["request"].user

        # Check if someone is trying to update a nest reserved by another user
        if instance.reserved_by and instance.reserved_by != user and not user.is_superuser:
            raise serializers.ValidationError("You cannot edit an observation reserved by another user.")

        # Only proceed if user has appropriate permissions
        if not user.is_superuser:
            user_municipality_ids = user.municipalities.values_list("id", flat=True)
            if instance.municipality and instance.municipality.id not in user_municipality_ids:
                raise PermissionDenied("You do not have permission to update nests in this municipality.")

        allowed_admin_fields = [
            "location",
            "nest_height",
            "nest_size",
            "nest_location",
            "nest_type",
            "wn_cluster_id",
            "admin_notes",
            "visible",
            "images",
            "reserved_by",
            "eradication_date",
            "eradicator_name",
            "eradication_duration",
            "eradication_persons",
            "eradication_result",
            "eradication_product",
            "eradication_method",
            "eradication_aftercare",
            "eradication_problems",
            "eradication_notes",
            "public_domain",
            "observer_received_email",
        ]

        # Eradication result logic
        eradication_result = validated_data.get("eradication_result")

        # Define eradication-related fields
        eradication_related_fields = [
            "eradication_date",
            "eradicator_name",
            "eradication_duration",
            "eradication_persons",
            "eradication_method",
            "eradication_aftercare",
            "eradication_problems",
            "eradication_notes",
            "eradication_product",
        ]

        # Only check for eradication fields that have non-null values
        has_eradication_fields = any(
            field in validated_data 
            and validated_data[field] is not None 
            for field in eradication_related_fields
        )
        
        if has_eradication_fields and eradication_result is None:
            raise serializers.ValidationError(
                "Eradication result is required when providing eradication-related fields."
            )

        # Automatically set eradication_date to today if eradication_result is present but eradication_date is not
        if eradication_result is not None and validated_data.get("eradication_date") is None:
            validated_data["eradication_date"] = datetime.now(timezone("EST")).date()

        # Further eradication result logic
        if eradication_result == EradicationResultEnum.SUCCESSFUL:
            validated_data["reserved_datetime"] = None
            validated_data["reserved_by"] = None

        if not user.is_superuser:
            # Non-admins cannot update admin-specific fields, so remove them
            admin_fields = ["admin_notes", "observer_received_email", "wn_admin_notes"]
            for field in admin_fields:
                if field in validated_data:
                    raise serializers.ValidationError(f"Field(s) {field}' can not be updated by non-admin users.")

        error_fields = []

        # Check if 'wn_cluster_id' is in validated_data and if it has changed
        if "wn_cluster_id" in validated_data and validated_data["wn_cluster_id"] != instance.wn_cluster_id:
            error_fields.append("wn_cluster_id")

        # If any fields are attempting to be updated, raise a ValidationError
        if error_fields:
            error_message = f"Following field(s) cannot be updated by any user: {', '.join(error_fields)}"
            raise serializers.ValidationError(error_message)

        # Conditionally set `reserved_by` and `reserved_datetime`
        if "reserved_by" in validated_data:
            if validated_data["reserved_by"] is not None:
                validated_data["reserved_datetime"] = datetime.now(timezone("EST"))
            else:
                validated_data["reserved_datetime"] = None

        for field in set(validated_data) - set(allowed_admin_fields):
            validated_data.pop(field)
        instance = super().update(instance, validated_data)
        return instance
    
    def to_internal_value(self, data: dict[str, Any]) -> dict[str, Any]:
        """Convert the incoming data to a Python native representation."""
        logger.info("Raw input data: %s", data)
        # List of fields that should be parsed as datetime (with time)
        datetime_fields = [
            "created_datetime",
            "modified_datetime",
            "wn_modified_datetime",
            "wn_created_datetime",
            "reserved_datetime",
            "observation_datetime",
        ]
        # List of fields that should be treated as date only (no time)
        date_fields = ["eradication_date"]

        # Process datetime fields to ensure they are properly converted to UTC
        for field in datetime_fields + date_fields:
            if data.get(field):
                if isinstance(data[field], str):
                    try:
                        converted_datetime = parse_and_convert_to_utc(data[field])
                        if field in date_fields:
                            converted_date = converted_datetime.date()
                            data[field] = converted_date
                        else:
                            data[field] = converted_datetime
                    except (ValueError, TypeError) as err:
                        logger.exception(f"Invalid datetime format for {field}: {data[field]}")
                        raise serializers.ValidationError({
                            field: [f"Invalid datetime format for {field}."]
                        }).with_traceback(err.__traceback__) from None
                else:
                    data[field] = data[field]  # Already a valid datetime

        # Handle location validation separately (if provided)
        if "location" in data:
            data["location"] = self.validate_location(data["location"])
        data.pop("wn_admin_notes", None)
        internal_data = super().to_internal_value(data)
        return dict(internal_data)

    def validate_location(self, value: Any) -> Point:
        """Validate the input location data. Handle different formats of location data."""
        if isinstance(value, Point):
            return value

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


class ExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Export
        fields = '__all__'
