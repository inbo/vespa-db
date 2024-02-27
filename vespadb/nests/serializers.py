"""Serializers for the nests app."""

from typing import ClassVar

from rest_framework import serializers

from vespadb.nests.models import Nest


class NestSerializer(serializers.ModelSerializer):
    """Serializer for the full details of a Nest model instance."""

    class Meta:
        """Meta class for the NestSerializer."""

        model = Nest
        fields = "__all__"


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
