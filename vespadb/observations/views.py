"""Views for the observations app."""

import csv
import logging
from typing import TYPE_CHECKING, Any
from urllib.parse import urlencode

from django.conf import settings
from django.core.cache import cache
from django.core.serializers import serialize
from django.db.models import Q, QuerySet
from django.http import HttpResponse, JsonResponse
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, BasePermission, IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework_gis.filters import DistanceToPointFilter

from vespadb.observations.filters import ObservationFilter
from vespadb.observations.models import Municipality, Observation
from vespadb.observations.serializers import (
    MunicipalitySerializer,
    ObservationPatchSerializer,
    ObservationSerializer,
)

if TYPE_CHECKING:
    from vespadb.users.models import VespaUser

logger = logging.getLogger(__name__)


class ObservationsViewSet(ModelViewSet):
    """ViewSet for the Observation model."""

    queryset = Observation.objects.all()
    serializer_class = ObservationSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        DistanceToPointFilter,
    ]
    filterset_fields = ["location", "created_datetime", "modified_datetime"]
    filterset_class = ObservationFilter
    ordering_fields = ["created_datetime", "modified_datetime"]
    distance_filter_field = "location"
    distance_filter_convert_meters = True

    def get_serializer_context(self) -> dict[str, Any]:
        """
        Add the request to the serializer context.

        :return: Context dictionary with the request included.
        """
        context: dict[str, Any] = super().get_serializer_context()
        context["request"] = self.request
        return context

    def get_serializer_class(self) -> BaseSerializer:
        """
        Return the class to use for the serializer. Defaults to using self.serializer_class.

        Admins get full serialization, others get basic serialization depending on the incoming request.

        :return: Serializer class
        """
        if self.request.method == "PATCH":
            return ObservationPatchSerializer
        return super().get_serializer_class()

    def get_permissions(self) -> list[BasePermission]:
        """Determine the set of permissions that apply to the current action.

        - For 'update' and 'partial_update' actions, authenticated users are allowed to make changes.
        - The 'destroy' action is restricted to admin users only.
        - All other actions are available to authenticated users for modification, with readonly access for unauthenticated users.

        Returns
        -------
            List[BasePermission]: A list of permission instances that should be applied to the action.
        """
        if self.action in {"create", "update", "partial_update"}:
            permission_classes = [IsAuthenticated()]
        elif self.action == "destroy":
            permission_classes = [IsAdminUser()]
        else:
            permission_classes = [AllowAny()]
        return permission_classes

    def get_queryset(self) -> QuerySet:
        """
        Return observations based on the reservation status and user privileges.

        Admin users can see all observations. Authenticated users see their reservations and unreserved observations.
        Unauthenticated users see only unreserved observations.
        """
        base_queryset: QuerySet = super().get_queryset()
        user = self.request.user

        # Check if the user is an admin; if true, return all observations
        if user.is_staff:
            return base_queryset

        # For authenticated users, filter by their reservations or non-reserved observations
        if user.is_authenticated:
            return base_queryset.filter(Q(reserved_by=None) | Q(reserved_by=user))

        # Unauthenticated users see only non-reserved observations
        return base_queryset.filter(reserved_by=None)

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Override the create method to determine the municipality for a new Observation instance based on the provided point location.

        Expects 'longitude' and 'latitude' in the request data.
        """
        data = request.data.copy()
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=["get"], permission_classes=[AllowAny])
    def geojson(self, request: Request) -> Response:
        """Serve Observation data in GeoJSON format."""
        query_params = request.query_params.dict()
        sorted_query_params_string = urlencode(sorted(query_params.items()))
        cache_key = f"observations_geojson_data_{sorted_query_params_string}"
        data = cache.get(cache_key)

        if not data:
            observations = self.get_queryset()
            data = serialize("geojson", observations, geometry_field="location", fields=("id", "location"))
            refresh_rate = settings.REDIS_REFRESH_RATE_MIN
            cache.set(cache_key, data, refresh_rate * 60)

        return HttpResponse(data, content_type="application/json")

    @action(detail=False, methods=["post"], permission_classes=[IsAdminUser])
    def bulk_import(self, request: Request) -> Response:
        """Allow bulk import of observations for admin users only.

        :param request: The request object.
        :return: HTTP Response indicating the status of the operation.
        """
        # Placeholder for bulk import logic.
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    @swagger_auto_schema(
        method="get",
        manual_parameters=[
            openapi.Parameter(
                "export_format",
                in_=openapi.IN_QUERY,
                description="Format of the exported data",
                type=openapi.TYPE_STRING,
                enum=["csv", "json"],
                default="csv",
            ),
        ],
    )
    @action(detail=False, methods=["get"], permission_classes=[AllowAny])
    def export(self, request: Request) -> Response:
        """Export observations data in the specified format."""
        user: VespaUser = request.user
        export_format = request.query_params.get("export_format", "json").lower()

        # Reuse the logic from `get_queryset` and `get_serializer_class`
        queryset = self.filter_queryset(self.get_queryset())
        serializer_class = self.get_serializer_class()

        # Context may include request info, if necessary for serialization
        serializer_context = self.get_serializer_context()
        serializer = serializer_class(queryset, many=True, context=serializer_context)

        # Serialize the data
        serialized_data = serializer.data

        # Export to JSON
        if export_format == "json":
            return JsonResponse(serialized_data, safe=False)

        # Export to CSV
        if export_format == "csv":
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = f'attachment; filename="observations_export_{user.username}.csv"'

            # Assuming `serialized_data` is a list of dictionaries
            if serialized_data:
                headers = serialized_data[0].keys()  # CSV column headers
                writer = csv.DictWriter(response, fieldnames=headers)
                writer.writeheader()
                writer.writerows(serialized_data)
            return response

        # Handle unsupported formats
        return Response({"error": "Unsupported format specified."}, status=status.HTTP_400_BAD_REQUEST)


class MunicipalityViewSet(ReadOnlyModelViewSet):
    """ViewSet for the Municipality model."""

    queryset = Municipality.objects.all().order_by("name")
    serializer_class = MunicipalitySerializer

    def get_permissions(self) -> list[BasePermission]:
        """Determine the set of permissions that apply to the current action."""
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAdminUser()]
