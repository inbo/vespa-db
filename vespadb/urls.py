"""Vespa-DB urls."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from vespadb.healthcheck import HealthCheckView

schema_view = get_schema_view(
    openapi.Info(
        title="Vespa-DB API Documentation",
        default_version="v1",
        description="API documentation for Vespa-DB. This API allows users to manage observations of Vespa velutina nests.",
        contact=openapi.Contact(email="vespawatch@inbo.be"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    re_path(r"^swagger(?P<format>\.json|\.yaml)$", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    path("admin/", admin.site.urls),
    path("", include("vespadb.observations.urls", namespace="observations")),
    path("", include("vespadb.users.urls", namespace="users")),
    path("health/", HealthCheckView.as_view(), name="health_check"),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
