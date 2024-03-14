"""vespadb URL Configuration."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.authtoken.views import obtain_auth_token
from vespadb.spa.views import SPAView

from vespadb.observations.views import map_view
from vespadb.users.views import login_view, profile_view, change_password_view, check_login

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
    path("api-token-auth/", obtain_auth_token, name="api_token_auth"),
    # observation views
    path("map/", map_view, name="map"),
    # User views
    path("login/", login_view, name="login"),
    path("check_login/", check_login, name="check_login"),
    #path('profile/', profile_view, name='user_profile'),
    #path('change_password/', change_password_view, name='change_password'),
    # Include the observations app URLs
    path("", include("vespadb.observations.urls", namespace="observations")),
    path("", include("vespadb.users.urls", namespace="users")),
    re_path(r'^.*$', SPAView.as_view(), name='spa'),
    # static urls
    *static(settings.STATIC_URL, document_root=settings.STATIC_ROOT),
]
