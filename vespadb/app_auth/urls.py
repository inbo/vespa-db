"""."""

from django.urls import path

from vespadb.app_auth.views import AuthCheck, ChangePasswordView, LoginView, LogoutView, expire_session_view

urlpatterns = [
    path("auth-check", AuthCheck.as_view(), name="auth_check"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),  # New change password endpoint
    path("expire-session/<str:session_key>/", expire_session_view, name="expire_session"),
]
