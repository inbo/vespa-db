"""Serializers for the observations app."""

import logging
from typing import TYPE_CHECKING, Any

from django.contrib.gis.geos import Point
from rest_framework import serializers
from rest_framework.request import Request

from vespadb.observations.models import Municipality, Observation
from vespadb.users.models import VespaUser

if TYPE_CHECKING:
    from rest_framework.request import Request

    from vespadb.users.models import VespaUser

logger = logging.getLogger(__name__)


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

        # Fields accessible by public (unauthenticated) users
        public_fields = [
            "id",
            "location",
            "nest_height",
            "nest_size",
            "nest_location",
            "nest_type",
            "created_by",
            "eradication_datetime",
            "municipality",
            "images",
        ]

        # Additional fields to show based on specific conditions
        conditional_fields = [
            "observer_phone_number",
            "observer_email",
            "observer_name",
            "observer_allows_contact",
            "observation_datetime",
        ]

        # Combine the lists for easier processing later
        all_fields = set(public_fields + conditional_fields)

        # Get the request from the context
        request: Request = self.context.get("request")

        # Default to filtering out certain fields unless conditions are met
        fields_to_include = public_fields

        # If the request exists and the user is authenticated
        if request and request.user.is_authenticated:
            # For non-admin authenticated users, check additional conditions
            if not request.user.is_staff:
                user: VespaUser = request.user
                # Check if user has personal_data_access and if the observation is in the user's province
                if (
                    user.personal_data_access
                    and instance.municipality
                    and user.municipalities
                    and instance.municipality.id in user.municipalities
                ):
                    # All conditions met, include all fields
                    fields_to_include = list(all_fields)
            else:
                # For admin users, include all fields
                fields_to_include = list(all_fields)
        else:
            # For unauthenticated users, limit to public fields
            fields_to_include = public_fields
        # Return data with only the fields to be included
        return {field: data[field] for field in fields_to_include if field in data}

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
            "modified_datetime",
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
        read_only_fields = [
            "id",
            "wn_id",
            "created_datetime",
            "location",
            "source",
            "wn_notes",
            "wn_admin_notes",
            "species",
            "wn_modified_datetime",
            "wn_created_datetime",
            "images",
            "municipality",
            "anb",
        ]


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
