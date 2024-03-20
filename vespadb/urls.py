"""vespadb URL Configuration."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from vespadb.users.views import UserStatusView

schema_view = get_schema_view(
    openapi.Info(
        title="Vespawatch API Documentation",
        default_version="v1",
        description="Vespawatch API Documentation",
        terms_of_service="",
        contact=openapi.Contact(email=""),
        license=openapi.License(name=""),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)
urlpatterns = [
    re_path(r"^swagger(?P<format>\.json|\.yaml)$", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    path("admin/", admin.site.urls),
    # User views
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("user_status/", UserStatusView.as_view(), name="user_status"),
    # Include the observations app URLs
    path("", include("vespadb.observations.urls", namespace="observations")),
    path("", include("vespadb.users.urls", namespace="users")),
]

if settings.DEBUG:
    urlpatterns = urlpatterns + static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT,
    )
