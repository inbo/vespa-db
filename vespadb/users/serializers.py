"""Serializer for the users app."""

import logging
from typing import Any

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from vespadb.users.models import VespaUser as User

logger = logging.getLogger(__name__)

POSTAL_CODE_LENGTH = 4


class UserSerializer(serializers.ModelSerializer):
    """User serializer."""

    class Meta:
        """Meta class for the UserSerializer."""

        model = User
        fields = ["id", "username", "email", "password", "date_joined", "postal_code", "province"]
        extra_kwargs = {
            "password": {"write_only": True, "required": False},
            "date_joined": {"read_only": True},
            "postal_code": {"required": True},
            "province": {"read_only": True},
        }

    def validate_postal_code(self, value: str) -> str:
        """Validate postal code."""
        if len(value) != POSTAL_CODE_LENGTH:
            raise serializers.ValidationError("Postal code must be 4 characters long.")

        if not value.isdigit():
            raise serializers.ValidationError("Postal code must contain only digits.")

        return value

    def to_representation(self, instance: User) -> dict[Any, Any]:
        """
        Override the default representation method to conditionally include 'postal_code' and 'province' for admin users.

        Args:
            instance (User): The user instance being serialized.

        Returns
        -------
            dict: The dictionary representation of the User instance, conditionally including sensitive fields.
        """
        ret: dict[Any, Any] = super().to_representation(instance)
        request = self.context.get("request", None)

        if request and (request.user.is_staff or request.user.is_superuser):
            ret["postal_code"] = instance.postal_code
            if instance.province:
                ret["province"] = instance.province.name
        else:
            ret.pop("postal_code", None)
            ret.pop("province", None)

        return ret

    def create(self, validated_data: dict[str, Any]) -> User:
        """Create a new user, ensuring the password is validated and hashed."""
        # Pop the password from validated_data to handle it separately
        password = validated_data.pop("password", None)

        if password is not None:
            try:
                validate_password(password)
            except DjangoValidationError as e:
                raise serializers.ValidationError({"password": list(e.messages)}) from e

        user: User = User.objects.create_user(**validated_data)

        if password is not None:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance: User, validated_data: dict[str, Any]) -> User:
        """Update a user, ensuring the password is validated and hashed if provided."""
        password = validated_data.pop("password", None)

        # Update fields except for password
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password is not None:
            try:
                validate_password(password, instance)
            except DjangoValidationError as e:
                raise serializers.ValidationError({"password": list(e.messages)}) from e
            instance.set_password(password)

        instance.save()
        return instance

    def validate_password(self, value: str) -> str:
        """Perform custom password validation."""
        if value is not None:
            try:
                # Use Django's built-in validators
                validate_password(value)
            except DjangoValidationError as exc:
                raise serializers.ValidationError(str(exc)) from exc
        return value


class LoginSerializer(serializers.Serializer):
    """Login serializer."""

    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate the user credentials."""
        username = attrs.get("username")
        password = attrs.get("password")
        user = authenticate(request=self.context.get("request"), username=username, password=password)
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        attrs["user"] = user
        return attrs
