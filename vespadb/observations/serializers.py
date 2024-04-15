"""Serializers for the observations app."""

import logging
from typing import TYPE_CHECKING, Any

from django.contrib.gis.geos import Point
from rest_framework import serializers
from rest_framework.request import Request

from vespadb.observations.models import Municipality, Observation

if TYPE_CHECKING:
    from rest_framework.request import Request

    from vespadb.users.models import VespaUser

logger = logging.getLogger(__name__)

# Define the fields that public users can read
public_read_fields = [
    "id",
    "location",
    "nest_height",
    "nest_size",
    "nest_location",
    "nest_type",
    "created_by",
    "eradication_datetime",
    "municipality",
    "province",
    "images",
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
    "eradication_result",
    "eradication_product",
    "eradication_notes",
    "municipality",
    "province",
    "anb",
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

    class Meta:
        """Meta class for the ObservationSerializer."""

        model = Observation
        fields = "__all__"

    def to_representation(self, instance: Observation) -> dict[str, Any]:
        """
        Dynamically filter fields based on user authentication status.

        :param instance: Observation instance.
        :return: A dictionary representation of the observation instance with filtered fields.
        """
        data: dict[str, Any] = super().to_representation(instance)
        request: Request = self.context.get("request")
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
            "reserved_datetime",
            "eradication_datetime",
            "eradicator_name",
            "eradication_result",
            "eradication_product",
            "eradication_notes",
        ]
        read_only_fields = [field for field in "__all__" if field not in user_read_fields]


class AdminObservationPatchSerializer(serializers.ModelSerializer):
    """Serializer for admin users allowing update operations on all fields of the Observation model. This serializer grants full access to all fields, including those that are typically restricted, providing admins with complete control over Observation records."""

    class Meta:
        """Meta class for the AdminObservationPatchSerializer."""

        model = Observation
        fields = "__all__"  # Admins can update all fields except id.
        read_only_fields = ("id",)


# Municipality serializers
class MunicipalitySerializer(serializers.ModelSerializer):
    """Serializer for the Municipality model."""

    class Meta:
        """Meta class for the MunicipalitySerializer."""

        model = Municipality
        fields = ["id", "name"]
