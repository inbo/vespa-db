"""Views for the users app."""

from django.contrib.auth.models import User
from rest_framework import serializers, viewsets
from rest_framework.permissions import AllowAny, BasePermission, IsAdminUser

from vespadb.permissions import IsAdminOrSelf
from vespadb.users.serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    """Viewset for the User model."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer: serializers.ModelSerializer) -> None:
        """Create a new user."""
        serializer.save()

    def get_permissions(self) -> list[BasePermission]:
        """Instantiate and return the list of permissions that this view requires."""
        if self.action in {"list", "create", "destroy"}:
            permission_classes = [IsAdminUser]
        elif self.action in {"retrieve", "update", "partial_update", "change_password"}:
            permission_classes = [IsAdminOrSelf]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]
