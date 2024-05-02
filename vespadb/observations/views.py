"""Views for the observations app."""

import csv
import json
import logging
from typing import TYPE_CHECKING, Any

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_ratelimit.decorators import ratelimit
from django.contrib.gis.db.models.functions import Transform
from django.contrib.gis.geos import GEOSGeometry
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db.models import CharField, OuterRef, Q, QuerySet, Subquery, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse, JsonResponse
from django.utils.timezone import now
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
BBOX_LENGTH = 4
REDIS_CACHE_EXPIRATION = 86400


class ObservationsViewSet(ModelViewSet):
    """ViewSet for the Observation model."""

    queryset = Observation.objects.all()
    serializer_class = ObservationSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        DistanceToPointFilter,
    ]
    ordering_fields = ["id", "municipality_name", "created_datetime", "modified_datetime"]
    filterset_fields = ["location", "created_datetime", "modified_datetime"]
    filterset_class = ObservationFilter
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
        base_queryset = super().get_queryset()
        order_params = self.request.query_params.get("ordering", "")

        if "municipality_name" in order_params:
            base_queryset = base_queryset.annotate(
                municipality_name=Coalesce(
                    Subquery(Municipality.objects.filter(id=OuterRef("municipality_id")).values("name")[:1]),
                    Value("Onbekend"),
                    output_field=CharField(),
                )
            )

        user = self.request.user

        # Check if the user is an admin; if true, return all observations
        if user.is_staff:
            return base_queryset

        # For authenticated users, filter by their reservations or non-reserved observations
        if user.is_authenticated:
            return base_queryset.filter(Q(reserved_by=None) | Q(reserved_by=user))

        # Unauthenticated users see only non-reserved observations
        return base_queryset.filter(reserved_by=None)

    def perform_update(self, serializer: BaseSerializer) -> None:
        """
        Set modified_by to the current user and modified_datetime to the current UTC time upon updating an observation.

        Parameters
        ----------
        serializer: BaseSerializer
            The serializer containing the validated data.
        """
        serializer.save(modified_by=self.request.user, modified_datetime=now())

    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Handle partial updates to an observation, especially for changes to 'reserved_by'.

        Parameters
        ----------
        - request (Request): The incoming HTTP request.
        - *args (Any): Additional positional arguments.
        - **kwargs (Any): Additional keyword arguments.

        Returns
        -------
        - Response: The HTTP response with the partial update result.
        """
        try:
            return super().partial_update(request, *args, **kwargs)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer: BaseSerializer) -> None:
        """
        Set created_by, modified_by to the current user and created_datetime, modified_datetime to the current UTC time upon creating an observation.

        Parameters
        ----------
        serializer: BaseSerializer
            The serializer containing the validated data.
        """
        serializer.save(
            created_by=self.request.user, modified_by=self.request.user, created_datetime=now(), modified_datetime=now()
        )

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

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Override the destroy method to update the reservation count when an observation is deleted.

        Parameters
        ----------
        - request (Request): The incoming HTTP request.
        - *args (Any): Additional positional arguments.
        - **kwargs (Any): Additional keyword arguments.

        Returns
        -------
        - Response: The HTTP response indicating the result of the delete operation.
        """
        observation = self.get_object()
        reserved_by = observation.reserved_by

        # Perform the standard delete operation
        response = super().destroy(request, *args, **kwargs)

        # If the observation was reserved, decrement the reservation count of the user
        if reserved_by:
            reserved_by.reservation_count -= 1
            reserved_by.save(update_fields=["reservation_count"])

        return response

    @method_decorator(ratelimit(key='ip', rate='15/m', method='GET', block=True))
    def get_paginated_response(self, data: list[dict[str, Any]]) -> Response:
        """
        Construct the paginated response for the observations data.

        This method adds pagination links and the total count of observations to the response.

        Parameters
        ----------
        - data (List[Dict[str, Any]]): Serialized data for the current page.

        Returns
        -------
        - Response: A response object containing the paginated data and navigation links.
        """
        assert self.paginator is not None
        return Response({
            "total": self.paginator.page.paginator.count,
            "next": self.paginator.get_next_link(),
            "previous": self.paginator.get_previous_link(),
            "results": data,
        })

    @method_decorator(ratelimit(key='ip', rate='15/m', method='GET', block=True))
    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Handle requests for the list of observations with pagination.

        Override the default list method to apply pagination and return paginated response.

        Parameters
        ----------
        - request (Request): The incoming HTTP request.
        - *args (Any): Additional positional arguments.
        - **kwargs (Any): Additional keyword arguments.

        Returns
        -------
        - Response: The paginated response containing the observations data or full list if pagination is not applied.
        """
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @method_decorator(ratelimit(key='ip', rate='15/m', method='GET', block=True))
    @action(detail=False, methods=["get"], url_path="dynamic-geojson")
    def geojson(self, request: Request) -> HttpResponse:
        """Return GeoJSON data based on the request parameters."""
        # Create a modified query dictionary excluding 'bbox'
        query_params = request.GET.copy()
        bbox_str = query_params.pop("bbox", None)

        # Sort parameters and create a cache key without 'bbox'
        sorted_params = "&".join(sorted(f"{key}={value}" for key, value in query_params.items()))
        cache_key = f"vespadb::{request.path}::{sorted_params}"
        logger.info(f"Checking cache for {cache_key}")

        # Attempt to get cached data
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.info("Cache hit - Returning cached response")
            return JsonResponse(cached_data, safe=False)

        bbox_str = request.GET.get("bbox")
        if bbox_str:
            try:
                bbox_coords = list(map(float, bbox_str.split(",")))
                if len(bbox_coords) == BBOX_LENGTH:
                    xmin, ymin, xmax, ymax = bbox_coords
                    bbox_wkt = f"POLYGON(({xmin} {ymin}, {xmin} {ymax}, {xmax} {ymax}, {xmax} {ymin}, {xmin} {ymin}))"
                    bbox = GEOSGeometry(bbox_wkt, srid=4326)
                else:
                    return HttpResponse("Invalid bbox format", status=status.HTTP_400_BAD_REQUEST)
            except ValueError:
                return HttpResponse("Invalid bbox values", status=status.HTTP_400_BAD_REQUEST)
        else:
            bbox = None

        # Apply filters
        queryset = self.filter_queryset(self.get_queryset())

        if bbox:
            queryset = queryset.filter(location__within=bbox)

        queryset = queryset.annotate(point=Transform("location", 4326))

        features = [
            {
                "type": "Feature",
                "properties": {"id": obs.id},
                "geometry": json.loads(obs.point.geojson) if obs.point else None,
            }
            for obs in queryset
        ]
        geojson_response = {"type": "FeatureCollection", "features": features}
        cache.set(cache_key, geojson_response, REDIS_CACHE_EXPIRATION)  # 24 hours
        return JsonResponse(geojson_response)

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
    @method_decorator(ratelimit(key='ip', rate='15/m', method='GET', block=True))
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
    pagination_class = None

    def get_permissions(self) -> list[BasePermission]:
        """Determine the set of permissions that apply to the current action."""
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAdminUser()]
