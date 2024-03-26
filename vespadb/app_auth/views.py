"""views for the app_auth app."""

from collections.abc import Sequence

from django.contrib.auth import login
from django.contrib.sessions.models import Session
from django.http import HttpResponseRedirect
from rest_framework import permissions, status
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from vespadb.app_auth.serializers import LoginSerializer, UserSerializer


class AuthCheck(APIView):
    """API view to check user authentication status."""

    permission_classes: list[BasePermission] = []

    def get(self, request: Request) -> Response:
        """
        Respond with user authentication status and user data if authenticated.

        Args:
            request (HttpRequest): The HTTP request object.

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
    permission_classes = (permissions.AllowAny,)

    def post(self, request: Request) -> Response:
        """
        Authenticate a user based on username and password.

        Args:
            request (HttpRequest): The HTTP request object.

        Returns
        -------
            Response: Status indicating the success or failure of the login attempt.
        """
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data
            login(request, user)
            return Response({"detail": "Login successful."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def expire_session_view(request: Request, session_key: str) -> HttpResponseRedirect:
    """
    View to expire a specific session.

    Args:
        request (HttpRequest): The HTTP request object.
        session_key (str): The key of the session to expire.

    Returns
    -------
        HttpResponseRedirect: Redirects to the session management page in admin.
    """
    try:
        session = Session.objects.get(session_key=session_key)
        session.delete()
    except Session.DoesNotExist:
        pass
    return HttpResponseRedirect("/admin/sessions/session/")
