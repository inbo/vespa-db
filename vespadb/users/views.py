"""Views for the users app."""

from django.contrib.auth.models import User
from rest_framework import serializers, viewsets
from typing import Optional
from vespadb.permissions import IsAdmin
from vespadb.users.serializers import UserSerializer
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from rest_framework.request import Request
from django import forms
from django.contrib.auth.models import User
from django.core.validators import EmailValidator
from vespadb.permissions import IsAdminOrSelf, IsAdmin
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.permissions import AllowAny, BasePermission
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django.http import JsonResponse
import json
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login

class UserViewSet(viewsets.ModelViewSet):
    """Viewset for the User model."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]

    def perform_create(self, serializer: serializers.ModelSerializer) -> None:
        """Create a new user."""
        serializer.save()
    
    def get_permissions(self) -> list[BasePermission]:
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list', 'create', 'destroy']:
            permission_classes = [IsAdmin]
        elif self.action in ['retrieve', 'update', 'partial_update', 'change_password']:
            permission_classes = [IsAdminOrSelf]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['post'])
    def change_password(self, request: Request, pk: Optional[int] = None) -> Response:
        """Change the password of the user."""
        user: User = self.get_object()
        if user != request.user:
            return Response({'message': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        confirm_new_password = request.data.get('confirm_new_password')
        
        if not user.check_password(old_password):
            return Response({'message': 'Old password is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if new_password != confirm_new_password:
            return Response({'message': 'New passwords do not match.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            validate_password(new_password, user)
            user.set_password(new_password)
            user.save()
            return Response({'message': 'Password changed successfully.'})
        except DjangoValidationError as e:
            return Response({'error': list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)

def login_view(request: Request) -> HttpResponse:
    if request.method == "POST":
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        username = data.get('username')
        password = data.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)  # Dit zorgt voor de sessie
            if request.content_type == 'application/json':
                # Stuur een eenvoudige succesmelding terug. De sessiecookie wordt automatisch ingesteld.
                return JsonResponse({'detail': 'Successfully logged in'})
            else:
                return HttpResponseRedirect(reverse('map'))  # Zorg dat deze verwijzing correct is
        else:
            if request.content_type == 'application/json':
                return JsonResponse({'detail': 'Invalid credentials'}, status=400)
            else:
                return render(request, "users/login.html", {"error": "Invalid credentials"})
    elif request.method == "GET":
        return render(request, "users/login.html")
    else:
        return HttpResponse(status=405)

def check_login(request: Request) -> HttpResponse:
    """Check if the user is logged in without using the @login_required decorator."""
    if request.user.is_authenticated:
        return JsonResponse({
            'isLoggedIn': True,
            'username': request.user.username,
            'user_id': request.user.id
        })
    else:
        return JsonResponse({'isLoggedIn': False}, status=200)  
      
def profile_view(request: Request) -> HttpResponse:
    """Render the profile view."""
    return render(request, "users/profile.html")

def change_password_view(request: Request) -> HttpResponse:
    """Render the profile view."""
    return render(request, "users/change_password.html")

