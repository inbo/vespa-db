"""Serializer for the users app."""

import logging
from typing import Any

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from vespadb.users.models import VespaUser as User

logger = logging.getLogger(__name__)


class UserSerializer(serializers.ModelSerializer):
    """User serializer."""

    class Meta:
        """Meta class for the UserSerializer."""

        model = User
        fields = ["id", "username", "email", "password", "date_joined", "municipalities", "personal_data_access"]
        extra_kwargs = {
            "password": {"write_only": True, "required": False},
            "date_joined": {"read_only": True},
            "municipalities": {"read_only": True},
            "personal_data_access": {"required": False},
        }

    def to_representation(self, instance: User) -> dict[Any, Any]:
        """
        Override the default representation method to conditionally include 'municipalities' for admin users.

        Args:
            instance (User): The user instance being serialized.

        Returns
        -------
            dict: The dictionary representation of the User instance, conditionally including sensitive fields.
        """
        ret: dict[Any, Any] = super().to_representation(instance)
        request = self.context.get("request", None)

        if request and (request.user.is_staff or request.user.is_superuser):
            if instance.municipalities:
                ret["municipalities"] = instance.municipalities
        else:
            ret.pop("municipalities", None)

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
