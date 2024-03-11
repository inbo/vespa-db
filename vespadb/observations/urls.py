"""vespadb Observations URL Configuration."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from vespadb.observations.views import ObservationsViewSet

app_name = "observations"

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"observations", ObservationsViewSet)

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("", include(router.urls)),
]
