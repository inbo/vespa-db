"""Serializer for the users app."""

import logging
from typing import Any

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from vespadb.users.models import VespaUser as User

logger = logging.getLogger(__name__)


class UserSerializer(serializers.ModelSerializer):
    """User serializer."""

    municipalities = serializers.SlugRelatedField(slug_field="name", many=True, read_only=True)
    permissions = serializers.SerializerMethodField()

    class Meta:
        """Meta class for the UserSerializer."""

        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "municipalities",
            "date_joined",
            "permissions",
            "reservation_count",
            "is_superuser",
        ]
        extra_kwargs = {
            "password": {"write_only": True, "required": False},
            "date_joined": {"read_only": True},
        }

    def get_permissions(self, obj: User) -> list[str]:
        """
        Retrieve all permissions for a given user.

        Args:
            obj (User): The user instance for which to retrieve permissions.

        Returns
        -------
            List[str]: A list of permission strings associated with the user.
        """
        return [obj.get_permission_level()]

    def create(self, validated_data: dict[str, Any]) -> User:
        """
        Create a new user, ensuring the password is validated and hashed.

        Args:
            validated_data (Dict[str, Any]): The validated data from the serializer.

        Returns
        -------
            User: The created user instance.
        """
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
        """
        Update a user, ensuring the password is validated and hashed if provided.

        Args:
            instance (User): The existing user instance to update.
            validated_data (Dict[str, Any]): The validated data from the serializer.

        Returns
        -------
            User: The updated user instance.
        """
        password = validated_data.pop("password", None)

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
        """
        Perform custom password validation.

        Args:
            value (str): The password value to validate.

        Returns
        -------
            str: The validated password value.

        Raises
        ------
            ValidationError: If the password validation fails.
        """
        if value is not None:
            try:
                validate_password(value)
            except DjangoValidationError as exc:
                raise serializers.ValidationError(str(exc)) from exc
        return value


class LoginSerializer(serializers.Serializer):
    """
    Serializer for handling user login.

    Validates the user's credentials and returns the user instance if successful,
    otherwise raises a ValidationError with an appropriate error message.
    """

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data: dict[str, Any]) -> User:
        """
        Validate user credentials.

        Args:
            data (Dict[str, Any]): A dictionary containing 'username' and 'password' keys.

        Returns
        -------
            User: The authenticated user object if credentials are valid.

        Raises
        ------
            ValidationError: If the username or password is incorrect.
        """
        user: User = User.objects.filter(username=data["username"]).first()
        if user and user.check_password(data["password"]):
            return user
        raise ValidationError({"error": "Invalid username or password."})


class ChangePasswordSerializer(serializers.Serializer):
    """Validate user input for changing password."""

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
