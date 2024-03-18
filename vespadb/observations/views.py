"""Views for the observations app."""

import csv
from urllib.parse import urlencode

from django.conf import settings
from django.core.cache import cache
from django.core.serializers import serialize
from django.http import HttpResponse
from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework_gis.filters import DistanceToPointFilter

from vespadb.observations.filters import ObservationFilter
from vespadb.observations.models import Observation
from vespadb.observations.serializers import (
    AdminObservationPatchSerializer,
    ObservationPatchSerializer,
    ObservationSerializer,
)
from vespadb.permissions import IsAdmin, IsUser


class ObservationsViewSet(viewsets.ModelViewSet):
    """ViewSet for the Observation model."""

    queryset = Observation.objects.all()
    serializer_class = ObservationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        DistanceToPointFilter,
    ]
    filterset_fields = ["location", "reported_datetime", "validation_status", "validated"]
    filterset_class = ObservationFilter
    ordering_fields = ["reported_datetime", "validated"]
    distance_filter_field = "location"
    distance_filter_convert_meters = True

    def get_serializer_class(self) -> BaseSerializer:
        """
        Return the class to use for the serializer. Defaults to using self.serializer_class.

        Admins get full serialization, others get basic serialization depending on the incoming request.

        :return: Serializer class
        """
        if self.request.method == "PATCH":
            if self.request.user.is_staff:
                return AdminObservationPatchSerializer
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
            permission_classes = [IsUser()]
        elif self.action == "destroy":
            permission_classes = [IsAdmin()]
        else:
            permission_classes = [AllowAny()]
        return permission_classes

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

    @action(detail=False, methods=["post"], permission_classes=[IsAdmin])
    def bulk_import(self, request: Request) -> Response:
        """Allow bulk import of observations for admin users only.

        :param request: The request object.
        :return: HTTP Response indicating the status of the operation.
        """
        # Placeholder for bulk import logic.
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    @action(detail=False, methods=["get"], permission_classes=[IsAdmin])
    def export(self, request: Request) -> HttpResponse:
        """
        Export observations data in CSV format for admin users only.

        :param request: The request object.
        :return: HTTP response with the CSV data.
        """
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="observations_export.csv"'

        writer = csv.writer(response)
        writer.writerow(["ID", "Creation Datetime", "Status", "Location", "Address"])  # Specify fields as needed.

        observations = Observation.objects.all().values_list("id", "creation_datetime", "status", "location", "address")
        for observation in observations:
            writer.writerow(observation)

        return response
