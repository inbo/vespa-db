"""URLs for the users app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from vespadb.users.views import AuthCheck, ChangePasswordView, LoginView, LogoutView, UserViewSet

app_name = "users"

router = DefaultRouter()
router.register(r"users", UserViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("auth-check", AuthCheck.as_view(), name="auth_check"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),
]
