"""Views for the users app."""
import json
from django.utils import timezone
from collections.abc import Sequence
from typing import Any
from django.contrib.auth import login, logout, update_session_auth_hash
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import AllowAny, BasePermission, IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.middleware.csrf import get_token

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from vespadb.permissions import IsAdminOrSelf
from vespadb.users.models import VespaUser as User
from vespadb.users.serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    UserSerializer,
)

class UserViewSet(viewsets.ModelViewSet):
    """Viewset for the User model."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer: serializers.ModelSerializer) -> None:
        """
        Create a new user.

        Args:
            serializer (serializers.ModelSerializer): The serializer instance.
        """
        serializer.save()

    def get_permissions(self) -> list[BasePermission]:
        """
        Instantiate and return the list of permissions that this view requires.

        Returns
        -------
            List[BasePermission]: List of permission instances.
        """
        if self.action in {"list", "create", "destroy"}:
            permission_classes = [IsAdminUser]
        elif self.action in {"retrieve", "update", "partial_update", "change_password"}:
            permission_classes = [IsAdminOrSelf]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]


class AuthCheck(APIView):
    """API view to check user authentication status."""

    permission_classes: list[BasePermission] = []

    def get(self, request: Request) -> Response:
        """
        Respond with user authentication status and user data if authenticated.

        Args:
            request (Request): The HTTP request object.

        Returns
        -------
            Response: Contains isAuthenticated flag and user data if authenticated.
        """
        if request.user.is_authenticated:
            user = UserSerializer(request.user, context={"request": request})
            return Response({"isAuthenticated": True, "user": user.data})
        return Response({"isAuthenticated": False})


class LoginView(APIView):
    """API view for user login."""

    authentication_classes: Sequence[type[BaseAuthentication]] = []
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="User Login",
        operation_description="Authenticate a user with a username and password, log them in, and return a CSRF token.",
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(
                description="Login successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Login successful."
                        ),
                        "csrftoken": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="abc123csrf"
                        )
                    },
                ),
            ),
            400: openapi.Response(
                description="Bad Request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Invalid username or password."
                        )
                    },
                ),
            ),
        },
    )
    def post(self, request: Request) -> Response:
        """
        Authenticate a user based on username and password, log them in, and return a CSRF token.
        """
        serializer = LoginSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data
        login(request, user)

        # Generate CSRF token
        csrf_token = get_token(request)

        # Prepare response
        response_data = {
            "detail": "Login successful.",
            "csrftoken": csrf_token
        }

        # Create the response and set CSRF token in both header and cookie
        response = Response(response_data, status=status.HTTP_200_OK)
        response.set_cookie(
            "csrftoken", csrf_token, httponly=False, secure=True, samesite="Lax"
        )
        response["X-CSRFToken"] = csrf_token  # Set CSRF token in response headers

        return response

class LogoutView(APIView):
    """API view for user logout."""

    def post(self, request: Request) -> Response:
        """
        Logout a user.

        Args:
            request (Request): The HTTP request object.

        Returns
        -------
            Response: Status indicating the success or failure of the logout attempt.
        """
        logout(request)
        return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    """API view to change user password."""

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Change the password of the authenticated user.

        Args:
            request (Request): The HTTP request object.

        Returns
        -------
            Response: Status indicating the success or failure of the password change.
        """
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data["old_password"]):
                return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(serializer.validated_data["new_password"])
            user.save()
            update_session_auth_hash(request, user)  # Important to keep the session active
            return Response({"detail": "Password changed successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
