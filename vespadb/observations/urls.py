"""Vespa-DB Observations URL Configuration."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from vespadb.observations.views import MunicipalityViewSet, ObservationsViewSet, ProvinceViewSet, search_address

app_name = "observations"

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"observations", ObservationsViewSet)
router.register(r"municipalities", MunicipalityViewSet)
router.register(r"provinces", ProvinceViewSet)

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("", include(router.urls)),
    path("search-address/", search_address, name="search_address"),
]
