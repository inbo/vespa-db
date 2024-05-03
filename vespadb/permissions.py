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


SYSTEM_USER_OBSERVATION_FIELDS_TO_UPDATE = [
    "location",
    "wn_notes",
    "wn_admin_notes",
    "species",
    "nest_height",
    "nest_size",
    "nest_location",
    "nest_type",
    "observer_phone_number",
    "observer_email",
    "observer_name",
    "observation_datetime",
    "wn_cluster_id",
    "wn_modified_datetime",
    "visible",
    "images",
    "municipality",
    "province",
    "anb",
]
