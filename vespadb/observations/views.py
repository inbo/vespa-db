"""Views for the observations app."""

import csv
import datetime
import io
import json
import time
import logging
import csv
import json
from typing import TYPE_CHECKING, Any, Union, Optional
from django.conf import settings
from django.http import FileResponse, HttpResponseNotFound
import os
from django.conf import settings

from django.contrib.gis.db.models.functions import Transform
from django.contrib.gis.geos import GEOSGeometry
from django.core.cache import cache
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import transaction
from django.db.models import CharField, OuterRef, QuerySet, Subquery, Value
from django.db.models.functions import Coalesce
from django.db.utils import IntegrityError
from django.http import HttpResponse, JsonResponse, HttpRequest
from django.db import connection
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.views.decorators.http import require_GET
from django_filters.rest_framework import DjangoFilterBackend
from django_ratelimit.decorators import ratelimit
from django.http import StreamingHttpResponse, HttpResponseBadRequest, HttpResponseNotFound, HttpResponseServerError
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from geopy.exc import GeocoderServiceError, GeocoderTimedOut
from geopy.geocoders import Nominatim
from rest_framework import filters, status
from rest_framework.decorators import action, parser_classes
from rest_framework.exceptions import NotFound
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, BasePermission, IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework_gis.filters import DistanceToPointFilter

from vespadb.observations.cache import invalidate_geojson_cache, invalidate_observation_cache
from vespadb.observations.filters import ObservationFilter
from vespadb.observations.helpers import parse_and_convert_to_utc
from vespadb.observations.models import Municipality, Observation, Province, Export
from vespadb.observations.models import Export
from vespadb.observations.tasks.generate_export import generate_export
from vespadb.observations.serializers import ObservationSerializer, MunicipalitySerializer, ProvinceSerializer

from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404

if TYPE_CHECKING:
    from geopy.location import Location

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class Echo:
    """An object that implements just the write method of the file-like interface."""
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


BBOX_LENGTH = 4
GEOJSON_REDIS_CACHE_EXPIRATION = 900  # 15 minutes
GET_REDIS_CACHE_EXPIRATION = 86400  # 1 day
BATCH_SIZE = 150
CSV_HEADERS = [
    "id", "created_datetime", "modified_datetime", "latitude", "longitude", "source", "source_id",
    "nest_height", "nest_size", "nest_location", "nest_type", "observation_datetime",
    "province", "eradication_date", "municipality", "images", "anb_domain",
    "notes", "eradication_result", "wn_id", "wn_validation_status", "nest_status"
]
class ObservationsViewSet(ModelViewSet):  # noqa: PLR0904
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
            if  self.request.user.is_superuser:
                permission_classes = [IsAdminUser()]
            elif self.request.user.is_authenticated and self.request.user.get_permission_level() == "logged_in_with_municipality":
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
        return base_queryset
    
    def perform_update(self, serializer: BaseSerializer) -> None:
        """
        Set modified_by to the current user and modified_datetime to the current UTC time upon updating an observation.

        Parameters
        ----------
        serializer: BaseSerializer
            The serializer containing the validated data.
        """
        user = self.request.user
        observation = self.get_object()

        if not user.is_superuser and "reserved_by" in self.request.data:
            user_municipality_ids = user.municipalities.values_list("id", flat=True)
            if observation.municipality and observation.municipality.id not in user_municipality_ids:
                raise PermissionDenied("You do not have permission to reserve nests in this municipality.")

        instance = serializer.save(modified_by=user, modified_datetime=now())
        invalidate_observation_cache(instance.id)
        invalidate_geojson_cache()

    @swagger_auto_schema(
        operation_description="Partially update an existing observation.",
        request_body=ObservationSerializer,
        responses={200: ObservationSerializer},
    )
    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Handle partial updates to an observation, especially for changes to 'reserved_by'."""
        data = request.data.copy()

        # Convert datetime fields to UTC if present
        datetime_fields = [
            "created_datetime",
            "modified_datetime",
            "wn_modified_datetime",
            "wn_created_datetime",
            "reserved_datetime",
            "observation_datetime",
            "eradication_date",
        ]
        for field in datetime_fields:
            if field in data:
                value = data[field]
                if value in {"", None}:
                    data[field] = None
                else:
                    try:
                        data[field] = parse_and_convert_to_utc(value).isoformat()
                    except (ValueError, TypeError):
                        return Response(
                            {field: [f"Invalid datetime format for {field}."]},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

        serializer = self.get_serializer(instance=self.get_object(), data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

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

    @swagger_auto_schema(
        operation_description="Create a new observation.",
        request_body=ObservationSerializer,
        responses={201: ObservationSerializer},
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

    @swagger_auto_schema(operation_description="Delete an observation by ID.", responses={204: "No Content"})
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

        try:
            response = super().destroy(request, *args, **kwargs)
            if reserved_by:
                reserved_by.reservation_count -= 1
                reserved_by.save(update_fields=["reservation_count"])
            # Invalidate the caches
            invalidate_observation_cache(observation.id)
            invalidate_geojson_cache()
            return response
        except Exception as e:
            logger.exception("Error during delete operation")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

    @method_decorator(ratelimit(key="ip", rate="60/m", method="GET", block=True))
    @swagger_auto_schema(
        operation_description="Retrieve a list of observations. Supports filtering and ordering.",
        responses={200: ObservationSerializer(many=True)},
    )
    def retrieve_list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
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

    @swagger_auto_schema(
        operation_description="Retrieve GeoJSON data for observations within a bounding box (bbox).",
        manual_parameters=[
            openapi.Parameter(
                "bbox",
                openapi.IN_QUERY,
                description="Bounding box for filtering observations. Format: xmin,ymin,xmax,ymax",
                type=openapi.TYPE_STRING,
            )
        ],
        responses={
            200: openapi.Response(
                "GeoJSON data",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "type": openapi.Schema(type=openapi.TYPE_STRING),
                        "features": openapi.Schema(
                            type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)
                        ),
                    },
                ),
            )
        },
    )
    @method_decorator(ratelimit(key="ip", rate="60/m", method="GET", block=True))
    @action(detail=False, methods=["get"], url_path="dynamic-geojson")
    def geojson(self, request: Request) -> HttpResponse:
        """Generate GeoJSON data for the observations."""
        try:
            query_params = request.GET.copy()
            bbox_str = query_params.pop("bbox", None)

            sorted_params = "&".join(sorted(f"{key}={value}" for key, value in query_params.items()))
            cache_key = f"vespadb::{request.path}::{sorted_params}"
            logger.info(f"Checking cache for {cache_key}")

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
                        bbox_wkt = (
                            f"POLYGON(({xmin} {ymin}, {xmin} {ymax}, {xmax} {ymax}, {xmax} {ymin}, {xmin} {ymin}))"
                        )
                        bbox = GEOSGeometry(bbox_wkt, srid=4326)
                    else:
                        return HttpResponse("Invalid bbox format", status=status.HTTP_400_BAD_REQUEST)
                except ValueError:
                    return HttpResponse("Invalid bbox values", status=status.HTTP_400_BAD_REQUEST)
            else:
                bbox = None

            queryset = self.filter_queryset(self.get_queryset())

            if bbox:
                queryset = queryset.filter(location__within=bbox)

            queryset = queryset.annotate(point=Transform("location", 4326))

            features = [
                {
                    "type": "Feature",
                    "properties": {
                        "id": obs.id,
                        "status": "eradicated"
                        if obs.eradication_result is not None
                        else "reserved"
                        if obs.reserved_by
                        else "default",
                    },
                    "geometry": json.loads(obs.location.geojson) if obs.location else None,
                }
                for obs in queryset
            ]
            geojson_response = {"type": "FeatureCollection", "features": features}
            cache.set(cache_key, geojson_response, GEOJSON_REDIS_CACHE_EXPIRATION)
            return JsonResponse(geojson_response)
        except Exception:
            logger.exception("An error occurred while generating GeoJSON data")
            return HttpResponse(
                "An error occurred while generating GeoJSON data", status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="Bulk import observations from either JSON or CSV file.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "file": openapi.Schema(type=openapi.TYPE_STRING, format="binary", description="CSV file"),
                "data": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_OBJECT),
                    description="JSON array of observation objects",
                ),
            },
            required=["data"],
        ),
        responses={200: "Success", 400: "Bad Request", 415: "Unsupported Media Type"},
    )
    @method_decorator(ratelimit(key="ip", rate="60/m", method="GET", block=True))
    @action(detail=False, methods=["post"], permission_classes=[IsAdminUser])
    @parser_classes([JSONParser, MultiPartParser, FormParser])
    def bulk_import(self, request: Request) -> Response:
        """Bulk import observations from either JSON or CSV file."""
        logger.info("Bulk import request received.")

        # Check content type
        content_type = request.content_type
        logger.info("Content type: %s", content_type)

        # Parse request data based on content type
        if content_type == "application/json":
            try:
                data = request.data.get("data", None)
                if not data:
                    return Response({"detail": "Empty data field in request body"}, status=status.HTTP_400_BAD_REQUEST)
            except ValueError as e:
                logger.exception("JSON parse error: %s", str(e))
                return Response({"detail": f"JSON parse error: {e!s}"}, status=status.HTTP_400_BAD_REQUEST)
        elif content_type.startswith("multipart/form-data"):
            file = request.FILES.get("file")
            if not file:
                logger.error("CSV file is required.")
                return Response({"error": "CSV file is required."}, status=status.HTTP_400_BAD_REQUEST)
            data = self.parse_csv(file)
        else:
            logger.error("Unsupported content type.")
            return Response({"error": "Unsupported content type."}, status=status.HTTP_400_BAD_REQUEST)

        logger.info("Bulk import request data: %s", data)

        # Process and validate data
        processed_data, errors = self.process_data(data)
        if errors:
            logger.error("Data validation errors: %s", errors)
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        # Save valid observations
        return self.save_observations(processed_data)

    @swagger_auto_schema(operation_description="Retrieve an observation by ID.", responses={200: ObservationSerializer})
    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Retrieve an observation by its ID.

        Parameters
        ----------
        - request (Request): The incoming HTTP request.
        - *args (Any): Additional positional arguments.
        - **kwargs (Any): Additional keyword arguments.

        Returns
        -------
        - Response: A response containing the serialized observation data.
        """
        instance = self.get_object()
        if not instance.visible:
            raise NotFound("This observation is not visible.")
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Update an existing observation.",
        request_body=ObservationSerializer,
        responses={200: ObservationSerializer},
    )
    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Update an existing observation.

        Parameters
        ----------
        - request (Request): The incoming HTTP request containing the observation data.
        - *args (Any): Additional positional arguments.
        - **kwargs (Any): Additional keyword arguments.

        Returns
        -------
        - Response: A response containing the updated serialized observation data.
        """
        return super().update(request, *args, **kwargs)

    def parse_csv(self, file: InMemoryUploadedFile) -> list[dict[str, Any]]:
        """Parse a CSV file to a list of dictionaries."""
        file.seek(0)
        reader = csv.DictReader(io.StringIO(file.read().decode("utf-8")))
        data = []
        for row in reader:
            try:
                if "source_id" in row:
                    row["source_id"] = int(row["source_id"]) if row["source_id"].isdigit() else None
                    
                logger.info(f"Original location data: {row['location']}")
                row["location"] = self.validate_location(row["location"])
                logger.info(f"Parsed location: {row['location']}")
                datetime_fields = [
                    "created_datetime",
                    "modified_datetime",
                    "observation_datetime",
                    "eradication_date",
                    "wn_modified_datetime",
                    "wn_created_datetime",
                ]
                for field in datetime_fields:
                    if row.get(field):
                        try:
                            row[field] = parse_and_convert_to_utc(row[field])
                        except (ValueError, TypeError) as e:
                            logger.exception(f"Invalid datetime format for {field}: {row[field]} - {e}")
                            row[field] = None
                data.append(row)
            except (ValueError, TypeError, ValidationError) as e:
                logger.exception(f"Error parsing row: {row} - {e}")
        return data

    def validate_location(self, location: str) -> GEOSGeometry:
        """Validate and convert location data."""
        try:
            if isinstance(location, str):
                if location.startswith("SRID"):
                    # Extract the actual point from the SRID string
                    point_str = location.split(";")[1].strip()
                    geom = GEOSGeometry(point_str, srid=4326)
                else:
                    geom = GEOSGeometry(location, srid=4326)
                logger.info(f"Validated GEOSGeometry: {geom}")
                return geom.wkt
            raise ValidationError("Invalid location data type")
        except (ValueError, TypeError) as e:
            logger.exception(f"Invalid location data: {location} - {e}")
            raise ValidationError("Invalid WKT format for location.") from e

    def process_data(self, data: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Process and validate the incoming data."""
        valid_observations = []
        errors = []
        for data_item in data:
            try:
                cleaned_item = self.clean_data(data_item)
                serializer = ObservationSerializer(data=cleaned_item)
                if serializer.is_valid():
                    valid_observations.append(serializer.validated_data)
                else:
                    errors.append(serializer.errors)
            except Exception as e:
                logger.exception(f"Error processing data item: {data_item} - {e}")
                errors.append({"error": str(e)})
        return valid_observations, errors

    def clean_data(self, data_dict: dict[str, Any]) -> dict[str, Any]:
        """Clean the incoming data and remove empty or None values."""
        logger.info("Original data item: %s", data_dict)
        data_dict.pop("id", None)

        datetime_fields = [
            "created_datetime",
            "modified_datetime",
            "observation_datetime",
            "eradication_date",
            "wn_modified_datetime",
            "wn_created_datetime",
        ]
        for field in datetime_fields:
            if data_dict.get(field):
                if isinstance(data_dict[field], str):
                    try:
                        data_dict[field] = parse_and_convert_to_utc(data_dict[field]).isoformat()
                    except (ValueError, TypeError):
                        logger.exception(f"Invalid datetime format for {field}: {data_dict[field]}")
                        data_dict.pop(field, None)
                elif isinstance(data_dict[field], datetime.datetime):
                    data_dict[field] = data_dict[field].isoformat()
                else:
                    data_dict.pop(field, None)

        # Convert empty strings to None for nullable fields
        nullable_fields = ["reserved_by", "eradication_result", "nest_size", "eradicator_name"]
        for field in nullable_fields:
            if not data_dict.get(field):
                data_dict[field] = None

        cleaned_data = {k: v for k, v in data_dict.items() if v not in [None, ""]}  # noqa: PLR6201
        logger.info("Cleaned data item: %s", cleaned_data)
        return cleaned_data

    def save_observations(self, valid_data: list[dict[str, Any]]) -> Response:
        """Save the valid observations to the database."""
        try:
            with transaction.atomic():
                Observation.objects.bulk_create([Observation(**data) for data in valid_data])
            return Response(
                {"message": f"Successfully imported {len(valid_data)} observations."}, status=status.HTTP_201_CREATED
            )
        except IntegrityError as e:
            logger.exception("Error during bulk import")
            return Response(
                {"error": f"An error occurred during bulk import: {e!s}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @method_decorator(ratelimit(key="ip", rate="60/m", method="GET", block=True))
    @action(detail=False, methods=["get"], permission_classes=[AllowAny])
    def export(self, request: HttpRequest) -> JsonResponse:
        """Initiate the export of observations and trigger a Celery task."""
        # Initialize the filterset
        filterset = self.filterset_class(data=request.GET, queryset=self.get_queryset())

        # Validate the filterset
        if not filterset.is_valid():
            return JsonResponse({"error": filterset.errors}, status=400)

        # Get the filtered queryset count first
        filtered_count = filterset.qs.count()
        if filtered_count > 10000:
            return JsonResponse({
                "error": f"Export too large. Found {filtered_count} records, maximum allowed is 10,000"
            }, status=400)

        # Prepare the filter parameters - only include valid filters
        filters = {}
        for key, value in request.GET.items():
            if key in filterset.filters and value:
                filters[key] = value

        # Create an Export record
        export = Export.objects.create(
            user=request.user if request.user.is_authenticated else None,
            filters=filters,
            status='pending',
        )

        # Trigger the Celery task
        task = generate_export.delay(
            export.id,
            filters,
            user_id=request.user.id if request.user.is_authenticated else None
        )

        # Update the Export record with the task ID
        export.task_id = task.id
        export.save()

        return JsonResponse({
            'export_id': export.id,
            'task_id': task.id,
            'total_records': filtered_count
        })
        
    @swagger_auto_schema(
        operation_description="Check the status of an export.",
        manual_parameters=[
            openapi.Parameter(
                'export_id',
                openapi.IN_QUERY,
                description="The ID of the export to check the status of.",
                type=openapi.TYPE_INTEGER,
                required=True,
            )
        ],
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                    'progress': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'error': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                    'download_url': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                },
            ),
            400: "Bad Request",
            404: "Export not found",
        },
    )
    @action(detail=False, methods=["get"])
    def export_status(self, request: HttpRequest) -> JsonResponse:
        """Check export status."""
        export_id = request.GET.get('export_id')
        if not export_id:
            logger.error("Export ID not provided")
            return JsonResponse({"error": "Export ID is required"}, status=400)
        
        try:
            export = get_object_or_404(Export, id=export_id)
        except Exception as e:
            logger.exception(f"Export ID {export_id} not found or invalid: {str(e)}")
            return JsonResponse({"error": f"Export ID {export_id} not found"}, status=404)
        
        if export.status == 'completed':
            download_url = request.build_absolute_uri(f'/observations/download_export/?export_id={export_id}')
            return JsonResponse({
                'status': 'completed',
                'download_url': download_url
            })

        return JsonResponse({
            'status': export.status,
            'progress': export.progress,
            'error': export.error_message
        })

    @action(detail=False, methods=["get"])
    def download_export(self, request: HttpRequest) -> Union[StreamingHttpResponse, HttpResponse]:
        """Stream the export directly to the user."""
        export_id = request.GET.get('export_id')
        if not export_id:
            return HttpResponseBadRequest("Export ID is required")

        try:
            export = Export.objects.get(id=export_id)
            if export.status != 'completed':
                return HttpResponseBadRequest("Export is not ready")

            # Get the data iterator from cache
            cache_key = f'export_{export_id}_data'
            rows = cache.get(cache_key)
            if not rows:
                return HttpResponseNotFound("Export data not found or expired")

            # Create the streaming response
            pseudo_buffer = Echo()
            writer = csv.writer(pseudo_buffer)
            response = StreamingHttpResponse(
                (writer.writerow(row) for row in rows),
                content_type='text/csv'
            )
            
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            response['Content-Disposition'] = f'attachment; filename="observations_export_{timestamp}.csv"'
            return response

        except Export.DoesNotExist:
            return HttpResponseNotFound("Export not found")
        except Exception as e:
            logger.error(f"Error streaming export: {str(e)}")
            return HttpResponseServerError("Error generating export")

@require_GET
def search_address(request: Request) -> JsonResponse:
    """
    Search for an address using the Nominatim geocoding service.

    This view function takes a GET request with a 'query' parameter containing
    the address to search for. It returns the latitude, longitude, and full
    address of the location if found.

    Parameters
    ----------
    request : django.http.HttpRequest
        The HTTP request object containing the 'query' parameter in GET data.

    Returns
    -------
    django.http.JsonResponse
        A JSON response containing either:
        - On success: latitude, longitude, and full address of the location
        - On failure: an error message with an appropriate HTTP status code

    Raises
    ------
    No exceptions are raised directly, but various HTTP status codes are returned:
    - 400: If no query is provided
    - 404: If the address is not found
    - 500: For any other exceptions during geocoding
    """
    query: str = request.GET.get("query", "")
    if not query:
        return JsonResponse({"error": "No query provided"}, status=400)

    geolocator: Nominatim = Nominatim(user_agent="vespa_db")
    try:
        location: Location | None = geolocator.geocode(query)
        if location:
            return JsonResponse({"lat": location.latitude, "lon": location.longitude, "address": location.address})
        return JsonResponse({"error": "Address not found"}, status=404)
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        return JsonResponse({"error": f"Geocoding service error: {e!s}"}, status=503)
    except (ValueError, TypeError) as e:
        return JsonResponse({"error": f"Unexpected error: {e!s}"}, status=500)


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

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "province_ids",
                openapi.IN_QUERY,
                description="Comma-separated list of province IDs",
                type=openapi.TYPE_STRING,
            )
        ]
    )
    @action(detail=False, methods=["get"])
    def by_provinces(self, request: Request) -> Response:
        """Return municipalities filtered by province IDs."""
        cache_key = "vespadb::municipalities_by_province::list"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        province_ids = request.query_params.get("province_ids")
        if not province_ids:
            return Response({"detail": "province_ids parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        province_ids = province_ids.split(",")
        municipalities = Municipality.objects.filter(province_id__in=province_ids).order_by("name")
        serializer = self.get_serializer(municipalities, many=True)
        cache.set(cache_key, serializer.data, GET_REDIS_CACHE_EXPIRATION)
        return Response(serializer.data)

    @method_decorator(ratelimit(key="ip", rate="60/m", method="GET", block=True))
    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Override the list method to add caching."""
        cache_key = "vespadb::municipalities::list"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, GET_REDIS_CACHE_EXPIRATION)
        return response


class ProvinceViewSet(ReadOnlyModelViewSet):
    """ViewSet for the Province model."""

    queryset = Province.objects.all().order_by("name")
    serializer_class = ProvinceSerializer
    pagination_class = None

    def get_permissions(self) -> list[BasePermission]:
        """Determine the set of permissions that apply to the current action."""
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAdminUser()]

    @method_decorator(ratelimit(key="ip", rate="60/m", method="GET", block=True))
    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Override the list method to add caching."""
        cache_key = "vespadb::provinces::list"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, GET_REDIS_CACHE_EXPIRATION)
        return response
