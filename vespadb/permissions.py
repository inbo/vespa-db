"""Permissies voor de observationen API."""

from django.contrib.auth.models import User
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import View


class IsUser(permissions.BasePermission):
    """Allow access only to authenticated users."""

    def has_permission(self, request: Request, view: View) -> bool:
        """Permission check for the user."""
        return bool(request.user and request.user.is_authenticated)


class IsAdmin(permissions.BasePermission):
    """Allow access only to admin users."""

    def has_permission(self, request: Request, view: View) -> bool:
        """Permission check for the admin."""
        return bool(request.user and request.user.is_staff)


class IsAdminOrSelf(permissions.BasePermission):
    """Custom permission to only allow users to edit their own profile unless they are an admin."""

    def has_object_permission(self, request: Request, view: View, obj: User) -> bool:
        """Write permissions are only allowed to the user themselves or an admin."""
        return bool(obj == request.user or request.user.is_staff)
