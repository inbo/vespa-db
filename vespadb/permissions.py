"""Permissies voor de observationen API."""

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import View

from vespadb.users.models import VespaUser as User


class IsAdminOrSelf(permissions.BasePermission):
    """Custom permission to only allow users to edit their own profile unless they are an admin."""

    def has_object_permission(self, request: Request, view: View, obj: User) -> bool:
        """Write permissions are only allowed to the user themselves or an admin."""
        return bool(obj == request.user or request.user.is_staff)
