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
from vespadb.observations.models import Municipality, Observation, Province, EradicationResultEnum
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
    "eradication_date",
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
]

# Define the conditional fields for authenticated users with specific permissions
conditional_fields = [
    "observer_phone_number",
    "observer_email",
    "observer_name",
]

# Fields that require special permissions (admins or specific user permissions)
admin_or_special_permission_fields = [
    "wn_validation_status",
    "wn_notes",
]


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
            "id": {"read_only": True, "help_text": "Unique ID for the observation."},
            "wn_id": {
                "required": False,
                "allow_null": True,
                "help_text": "Unique ID for the observation in the source system.",
            },
            "created_datetime": {"help_text": "Datetime when the observation was created."},
            "modified_datetime": {"help_text": "Datetime when the observation was last modified."},
            "location": {"help_text": "Geographical location of the observation as a point."},
            "source": {"help_text": "Source of the observation."},
            "wn_notes": {"help_text": "Notes about the observation."},
            "wn_admin_notes": {"help_text": "Admin notes about the observation."},
            "wn_validation_status": {"help_text": "Validation status of the observation."},
            "species": {"help_text": "Species of the observed nest."},
            "nest_height": {"help_text": "Height of the nest."},
            "nest_size": {"help_text": "Size of the nest."},
            "nest_location": {"help_text": "Location of the nest."},
            "nest_type": {"help_text": "Type of the nest."},
            "observer_phone_number": {"help_text": "Phone number of the observer."},
            "observer_email": {"help_text": "Email of the observer."},
            "observer_received_email": {"help_text": "Flag indicating if observer received email."},
            "observer_name": {"help_text": "Name of the observer."},
            "observation_datetime": {"help_text": "Datetime when the observation was made."},
            "wn_cluster_id": {"required": False, "allow_null": True, "help_text": "Cluster ID of the observation."},
            "admin_notes": {
                "required": False,
                "allow_blank": True,
                "allow_null": True,
                "help_text": "Admin notes for the observation.",
            },
            "wn_modified_datetime": {"help_text": "Datetime when the observation was modified in the source system."},
            "wn_created_datetime": {"help_text": "Datetime when the observation was created in the source system."},
            "visible": {"help_text": "Flag indicating if the observation is visible."},
            "images": {
                "required": False,
                "allow_null": True,
                "help_text": "List of images associated with the observation.",
            },
            "reserved_by": {"required": False, "allow_null": True, "help_text": "User who reserved the observation."},
            "reserved_datetime": {"help_text": "Datetime when the observation was reserved."},
            "eradication_date": {
                "required": False,
                "allow_null": True,
                "help_text": "Date when the nest was eradicated.",
            },
            "eradicator_name": {"help_text": "Name of the person who eradicated the nest."},
            "eradication_duration": {"help_text": "Duration of the eradication."},
            "eradication_persons": {"help_text": "Number of persons involved in the eradication."},
            "eradication_result": {"help_text": "Result of the eradication."},
            "eradication_product": {"help_text": "Product used for the eradication."},
            "eradication_method": {"help_text": "Method used for the eradication."},
            "eradication_aftercare": {"help_text": "Aftercare result of the eradication."},
            "eradication_problems": {"help_text": "Problems encountered during the eradication."},
            "eradication_notes": {"help_text": "Notes about the eradication."},
            "municipality": {"help_text": "Municipality where the observation was made."},
            "province": {"help_text": "Province where the observation was made."},
            "anb": {"help_text": "Flag indicating if the observation is in ANB area."},
            "public_domain": {"help_text": "Flag indicating if the observation is in the public domain."},
        }

    def get_municipality_name(self, obj: Observation) -> str | None:
        """Retrieve the name of the municipality associated with the observation, if any."""
        return obj.municipality.name if obj.municipality else None

    def get_status(self, obj: Observation) -> str:
        """Determine the status of the observation based on its properties."""
        if obj.eradication_date:
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
            "eradication_date",
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
                    fields_to_include = set(user_read_fields + conditional_fields + admin_or_special_permission_fields)
                else:
                    fields_to_include = set(user_read_fields + conditional_fields)
                # Filter the data to include only the permitted fields
                filtered_data = {field: data[field] for field in fields_to_include if field in data}
                return filtered_data
            # If user is staff, return all fields as is, no need to modify `data`
            return data
        # For unauthenticated or public access, restrict to public_read_fields
        return {field: data[field] for field in public_read_fields if field in data}

    def validate_reserved_by(self, value: VespaUser) -> VespaUser:
        """Validate that the user does not exceed the maximum number of allowed reservations and has permission to reserve in the specified municipality."""
        if value:
            current_reservations_count = Observation.objects.filter(
                reserved_by=value, eradication_date__isnull=True
            ).count()
            if current_reservations_count >= settings.MAX_RESERVATIONS:
                logger.error(f"User {value.id} exceeded the reservation limit.")
                raise ValidationError(
                    f"This user has already reached the maximum number of reservations ({settings.MAX_RESERVATIONS})."
                )
            request = self.context.get("request")
            if request and not request.user.is_staff:
                observation_municipality = self.instance.municipality if self.instance else None
                user_municipality_ids = request.user.municipalities.values_list("id", flat=True)
                if observation_municipality and observation_municipality.id not in user_municipality_ids:
                    raise ValidationError("You do not have permission to reserve nests in this municipality.")
        return value

    def update(self, instance: Observation, validated_data: dict[Any, Any]) -> Observation:
        """Update method to handle observation reservations."""
        user = self.context["request"].user

        # Eradication result logic
        eradication_result = validated_data.get('eradication_result')
        if eradication_result == EradicationResultEnum.SUCCESSFUL:
            validated_data['reserved_datetime'] = None
            validated_data['reserved_by'] = None
            validated_data['eradication_date'] = timezone.now()
        elif eradication_result in [
            EradicationResultEnum.UNSUCCESSFUL,
            EradicationResultEnum.UNTREATED,
            EradicationResultEnum.UNKNOWN,
        ]:
            validated_data['eradication_date'] = None

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

        # Allow admins to update following fields
        if user.is_staff:
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
            for field in set(validated_data) - set(allowed_admin_fields):
                validated_data.pop(field)
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
            "eradication_date",
            "eradicator_name",
            "eradication_result",
            "eradication_product",
            "eradication_method",
            "eradication_problems",
            "eradication_notes",
            "eradication_aftercare",
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
            "eradication_date",
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
