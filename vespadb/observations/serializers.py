"""Serializers for the observations app."""

import logging
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework import serializers
from rest_framework.request import Request

from vespadb.observations.models import Municipality, Observation
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
    "notes",
    "modified_by",
    "created_by",
    "wn_modified_datetime",
    "wn_created_datetime",
    "duplicate",
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
]

# Define the conditional fields for authenticated users with specific permissions
conditional_fields = [
    "observer_phone_number",
    "observer_email",
    "observer_name",
    "observer_allows_contact",
    "observation_datetime",
]


# Observation serializers
class ObservationSerializer(serializers.ModelSerializer):
    """Serializer for the full details of a Observation model instance."""

    municipality_name = serializers.SerializerMethodField()

    class Meta:
        """Meta class for the ObservationSerializer."""

        model = Observation
        fields = "__all__"

    def get_municipality_name(self, obj: Observation) -> str | None:
        """
        Retrieve the name of the municipality associated with the observation, if any.

        Parameters
        ----------
        obj (Observation): The Observation instance.

        Returns
        -------
        Optional[str]: The name of the municipality or None if not available.
        """
        return obj.municipality.name if obj.municipality else None

    def to_representation(self, instance: Observation) -> dict[str, Any]:
        """
        Dynamically filter fields based on user authentication status.

        :param instance: Observation instance.
        :return: A dictionary representation of the observation instance with filtered fields.
        """
        data: dict[str, Any] = super().to_representation(instance)
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

    def validate_location(self, value: dict[str, float]) -> Point:
        """Validate the input location data. Override this method to implement custom validation logic as needed.

        Parameters
        ----------
        - value (Dict[str, float]): The location data to validate, expected to be a dictionary
          with 'latitude' and 'longitude' keys.

        Returns
        -------
        - Point: The validated location data.

        """
        latitude = value.get("latitude")
        longitude = value.get("longitude")

        if latitude is None or longitude is None:
            raise serializers.ValidationError("Missing or invalid location data")

        return Point(longitude, latitude)


class ObservationPatchSerializer(serializers.ModelSerializer):
    """Serializer for patching observations with limited fields accessible by exterminators or other specific roles. This serializer allows updating a subset of the Observation model's fields, ensuring that users can only modify fields they are authorized to."""

    class Meta:
        """Meta class for the ObservationPatchSerializer."""

        model = Observation
        fields = [
            "nest_height",
            "nest_size",
            "nest_location",
            "nest_type",
            "notes",
            "modified_by",
            "created_by",
            "duplicate",
            "reserved_by",
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
        ]
        read_only_fields = [field for field in "__all__" if field not in user_read_fields]

    def validate_reserved_by(self, value: VespaUser) -> VespaUser:
        """
        Validate that the user does not exceed the maximum number of allowed reservations.

        :param value: The user instance to be set as reserved_by.
        :return: The validated user instance.
        :raises ValidationError: If the user exceeds the maximum number of reservations.
        """
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
        """
        Update method to handle observation reservations.

        This method checks if the `reserved_by` field is being updated. If it is and the current value is None,
        it sets `reserved_datetime` to the current time and updates `reserved_by` to the current user.

        It also prevents non-admin users from updating observations that are reserved by someone else.

        Parameters
        ----------
            instance (Observation): The observation instance that is being updated.
            validated_data (dict): Dictionary of new data for the observation.

        Returns
        -------
            Observation: The updated observation instance.

        Raises
        ------
            serializers.ValidationError: If a non-admin user tries to update an observation reserved by another user.
        """
        user = self.context["request"].user

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
            "duplicate",
            "reserved_by",
            "eradication_datetime",
            "eradicator_name",
            "eradication_result",
            "eradication_product",
            "eradication_notes",
        ]

        for field in set(validated_data) - set(allowed_fields):
            validated_data.pop(field)

        instance = super().update(instance, validated_data)
        return instance


# Municipality serializers
class MunicipalitySerializer(serializers.ModelSerializer):
    """Serializer for the Municipality model."""

    class Meta:
        """Meta class for the MunicipalitySerializer."""

        model = Municipality
        fields = ["id", "name"]
