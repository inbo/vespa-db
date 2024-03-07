"""Serializers for the observations app."""

from typing import Any, ClassVar, cast

from django.contrib.gis.geos import Point
from rest_framework import serializers
from vespadb.observations.models import Cluster
from django.utils import timezone

from vespadb.observations.models import Observation

# Observation serializers
class ObservationSerializer(serializers.ModelSerializer):
    """Serializer for the full details of a Observation model instance."""

    class Meta:
        """Meta class for the ObservationSerializer."""

        model = Observation
        fields = "__all__"

    def validate_location(self, value: dict[str, float]) -> dict[str, float]:
        """Validate the input location data. Override this method to implement custom validation logic as needed.

        Parameters
        ----------
        - value (Dict[str, float]): The location data to validate, expected to be a dictionary
          with 'latitude' and 'longitude' keys.

        Returns
        -------
        - Dict[str, float]: The validated location data.

        """
        # Custom validation logic can be implemented here
        return value

    def create(self, validated_data: dict[str, Any]) -> Observation:
        """Create a Observation instance from validated data, converting location data from a dictionary to a Point object suitable for the GeoDjango field.

        Parameters
        ----------
        - validated_data (Dict[str, Any]): The data validated by the serializer.

        Returns
        -------
        - Observation: The created Observation instance.
        """
        location_data = validated_data.pop("location", {})
        latitude = location_data.get("latitude")
        longitude = location_data.get("longitude")

        if latitude is not None and longitude is not None:
            validated_data["location"] = Point(longitude, latitude)
        else:
            # Handle missing location data, e.g., by raising a validation error
            raise serializers.ValidationError("Missing or invalid location data")

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
        location_data = validated_data.pop("location", {})
        latitude = location_data.get("latitude")
        longitude = location_data.get("longitude")

        if latitude is not None and longitude is not None:
            validated_data["location"] = Point(longitude, latitude)
        else:
            # Handle missing location data, e.g., by raising a validation error
            raise serializers.ValidationError("Missing or invalid location data")
        
        # Set last_modification_datetime to now
        instance.last_modification_datetime = timezone.now()

        return cast(Observation, super().update(instance, validated_data))


class ObservationPatchSerializer(serializers.ModelSerializer):
    """Serializer for updating observations by exterminators with limited fields."""

    class Meta:
        """Meta class for the ObservationPatchSerializer."""

        model = Observation
        # Specify the fields that can be updated by users.
        fields: ClassVar[list[str]] = ["source", "validation_status"]
        read_only_fields: ClassVar[list[str]] = ["validation_status", "exterminator", "extermination_datetime"]


class AdminObservationPatchSerializer(serializers.ModelSerializer):
    """Serializer for updating observations by admin users with access to all fields."""

    class Meta:
        """Meta class for the AdminObservationPatchSerializer."""

        model = Observation
        fields = "__all__"  # Admins can update all fields.


# Cluster serializers
class ClusterSerializer(serializers.ModelSerializer):
    """Serializer for the full details of a Cluster model instance."""

    class Meta:
        """Meta class for the ClusterSerializer."""

        model = Cluster
        fields = "__all__"

class ClusterPatchSerializer(serializers.ModelSerializer):
    """Serializer for updating clusters with limited fields."""

    class Meta:
        """Meta class for the ClusterPatchSerializer."""

        model = Cluster
        # Specify the fields that can be updated by users.
        fields: ClassVar[list[str]] = ["species", "admin_notes"]
        read_only_fields: ClassVar[list[str]] = ["location", "creation_datetime", "last_modification_datetime"]


class AdminClusterPatchSerializer(serializers.ModelSerializer):
    """Serializer for updating clusters by admin users with access to all fields."""

    class Meta:
        """Meta class for the AdminClusterPatchSerializer."""

        model = Cluster
        fields = "__all__"  # Admins can update all fields.