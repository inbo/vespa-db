"""Serializers for the observations app."""

from typing import Any, cast

from django.contrib.gis.geos import Point
from django.utils import timezone
from rest_framework import serializers

from vespadb.observations.models import Municipality, Observation


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
        public_fields = ["id", "location", "nest_height", "nest_size", "nest_location", "nest_type", "created_by"]

        # Check if the request exists and if the user is authenticated
        request = self.context.get("request", None)
        if request and not request.user.is_authenticated:
            # Restrict data to only public fields
            return {field: data[field] for field in public_fields if field in data}
        return data

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

    def create(self, validated_data: dict[str, Any]) -> Observation:
        """Create a Observation instance from validated data, converting location data from a dictionary to a Point object suitable for the GeoDjango field.

        Parameters
        ----------
        - validated_data (Dict[str, Any]): The data validated by the serializer.

        Returns
        -------
        - Observation: The created Observation instance.
        """
        return cast(Observation, super().create(validated_data))

    def update(self, instance: Observation, validated_data: dict[str, Any]) -> Observation:
        """Update an existing Observation instance with validated data, converting location data from a dictionary to a Point object when necessary.

        Parameters
        ----------
        - instance (Observation): The Observation instance to update.
        - validated_data (Dict[str, Any]): The data validated by the serializer.

        Returns
        -------
        - Observation: The updated Observation instance.
        """
        # Set last_modification_datetime to now
        instance.last_modification_datetime = timezone.now()

        return cast(Observation, super().update(instance, validated_data))


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
            "eradication_datetime",
            "eradicator_name",
            "eradication_result",
            "eradication_product",
            "eradication_notes",
            "duplicate",
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
            "wn_cluster_id",
            "wn_modified_datetime",
            "wn_created_datetime",
            "images",
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
        geo_field = "polygon"
        fields = ["name", "nis_code", "polygon"]
