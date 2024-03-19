"""Views for the users app."""

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, BasePermission
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from vespadb.permissions import IsAdmin, IsAdminOrSelf
from vespadb.users.serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    """Viewset for the User model."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]

    def perform_create(self, serializer: serializers.ModelSerializer) -> None:
        """Create a new user."""
        serializer.save()

    def get_permissions(self) -> list[BasePermission]:
        """Instantiate and return the list of permissions that this view requires."""
        if self.action in {"list", "create", "destroy"}:
            permission_classes = [IsAdmin]
        elif self.action in {"retrieve", "update", "partial_update", "change_password"}:
            permission_classes = [IsAdminOrSelf]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]

    @action(detail=True, methods=["post"])
    def change_password(self, request: Request, pk: int | None = None) -> Response:
        """Change the password of the user."""
        user: User = self.get_object()
        if user != request.user:
            return Response({"message": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        confirm_new_password = request.data.get("confirm_new_password")

        if not user.check_password(old_password):
            return Response({"message": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_new_password:
            return Response({"message": "New passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(new_password, user)
            user.set_password(new_password)
            user.save()
            return Response({"message": "Password changed successfully."})
        except DjangoValidationError as e:
            return Response({"error": list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)


class UserStatusView(APIView):
    """View to check if a user is logged in."""

    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        """Return user status."""
        user: User = request.user
        if user.is_authenticated:
            return Response({"is_logged_in": True, "username": user.username, "user_id": user.id})
        return Response({"is_logged_in": False}, status=status.HTTP_401_UNAUTHORIZED)
