"""URLs for the users app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from vespadb.users.views import UserViewSet

app_name = "users"

router = DefaultRouter()
router.register(r"users", UserViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
