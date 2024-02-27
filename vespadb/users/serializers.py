"""Serializers for the users app."""

from typing import Any

from django.contrib.auth.models import User
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model."""

    class Meta:
        """Meta class for the UserSerializer."""

        model = User
        fields = ["id", "username", "email", "password", "date_joined"]
        extra_kwargs = {"password": {"write_only": True}, "date_joined": {"read_only": True}}

    def create(self, validated_data: dict[str, Any]) -> User:
        """Create a new user."""
        return User.objects.create_user(**validated_data)
