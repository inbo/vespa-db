"""Serializers for the nests app."""

from typing import Any, ClassVar, cast

from django.contrib.gis.geos import Point
from rest_framework import serializers

from vespadb.nests.models import Nest


class NestSerializer(serializers.ModelSerializer):
    """Serializer for the full details of a Nest model instance."""

    class Meta:
        """Meta class for the NestSerializer."""

        model = Nest
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

    def create(self, validated_data: dict[str, Any]) -> Nest:
        """Create a Nest instance from validated data, converting location data from a dictionary to a Point object suitable for the GeoDjango field.

        Parameters
        ----------
        - validated_data (Dict[str, Any]): The data validated by the serializer.

        Returns
        -------
        - Nest: The created Nest instance.
        """
        location_data = validated_data.pop("location", {})
        latitude = location_data.get("latitude")
        longitude = location_data.get("longitude")

        if latitude is not None and longitude is not None:
            validated_data["location"] = Point(longitude, latitude)
        else:
            # Handle missing location data, e.g., by raising a validation error
            raise serializers.ValidationError("Missing or invalid location data")

        return cast(Nest, super().create(validated_data))

    def update(self, instance: Nest, validated_data: dict[str, Any]) -> Nest:
        """Update an existing Nest instance with validated data, converting location data from a dictionary to a Point object when necessary.

        Parameters
        ----------
        - instance (Nest): The Nest instance to update.
        - validated_data (Dict[str, Any]): The data validated by the serializer.

        Returns
        -------
        - Nest: The updated Nest instance.
        """
        location_data = validated_data.pop("location", {})
        latitude = location_data.get("latitude")
        longitude = location_data.get("longitude")

        if latitude is not None and longitude is not None:
            validated_data["location"] = Point(longitude, latitude)
        else:
            # Handle missing location data, e.g., by raising a validation error
            raise serializers.ValidationError("Missing or invalid location data")

        return cast(Nest, super().update(instance, validated_data))


class NestPatchSerializer(serializers.ModelSerializer):
    """Serializer for updating nests by exterminators with limited fields."""

    class Meta:
        """Meta class for the NestPatchSerializer."""

        model = Nest
        # Specify the fields that can be updated by exterminators.
        fields: ClassVar[list[str]] = ["public_domain", "nature_reserve"]
        read_only_fields: ClassVar[list[str]] = ["status", "exterminator", "extermination_datetime"]


class AdminNestPatchSerializer(serializers.ModelSerializer):
    """Serializer for updating nests by admin users with access to all fields."""

    class Meta:
        """Meta class for the AdminNestPatchSerializer."""

        model = Nest
        fields = "__all__"  # Admins can update all fields.
