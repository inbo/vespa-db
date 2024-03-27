"""Serializers for the app_auth app."""

from typing import Any

from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class UserSerializer(serializers.ModelSerializer):
    """IUser serializer for the User model."""

    permissions = serializers.SerializerMethodField()

    def get_permissions(self, obj: User) -> list[str]:
        """
        Retrieve all permissions for a given user.

        Args:
            obj (User): The user instance for which to retrieve permissions.

        Returns
        -------
            list[str]: A list of permission strings associated with the user.
        """
        return list(obj.get_all_permissions())

    class Meta:
        """."""

        model = User
        fields = ["id", "username", "first_name", "last_name", "permissions"]


class LoginSerializer(serializers.Serializer):
    """
    Serializer for handling user login.

    Validates the user's credentials and returns the user instance if successful,
    otherwise raises a ValidationError with an appropriate error message.
    """

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data: dict[Any, Any]) -> User:
        """
        Validate user credentials.

        Args:
            data (Dict[Any, Any]): A dictionary containing 'username' and 'password' keys.

        Returns
        -------
            User: The authenticated user object if credentials are valid.

        Raises
        ------
            ValidationError: If the username or password is incorrect.
        """
        user = User.objects.filter(username=data["username"]).first()
        if user and user.check_password(data["password"]):
            return user
        raise ValidationError({"error": "Invalid username or password."})


class ChangePasswordSerializer(serializers.Serializer):
    """Validate user input for changing password."""

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
