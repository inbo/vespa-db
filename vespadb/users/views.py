"""Views for the users app."""

from django.contrib.auth.models import User
from rest_framework import serializers, viewsets

from vespadb.permissions import IsAdmin
from vespadb.users.serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    """Viewset for the User model."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]

    def perform_create(self, serializer: serializers.ModelSerializer) -> None:
        """Create a new user."""
        serializer.save()
