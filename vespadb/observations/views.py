"""Views for the observations app."""
import datetime
import io
import json
import logging
import json
import csv
from typing import TYPE_CHECKING, Any, Any, Union, TextIO, Union, List, Set, Optional
import datetime
import tempfile
import os
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_log,
    after_log,
)
import time
from typing import Generator, Optional
from django.db import OperationalError, connection, transaction
from django.core.exceptions import ValidationError
import psycopg2
from django.http import FileResponse
import os 
import tempfile

from django.contrib.gis.db.models.functions import Transform
from django.contrib.gis.geos import GEOSGeometry
from django.core.cache import cache
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import CharField, OuterRef, QuerySet, Subquery, Value
from django.db.models.functions import Coalesce
from django.db.utils import IntegrityError
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse, HttpRequest
from django.db import connection
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.views.decorators.http import require_GET
from django_filters.rest_framework import DjangoFilterBackend
from django_ratelimit.decorators import ratelimit
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
from vespadb.observations.serializers import user_read_fields, public_read_fields

from vespadb.observations.cache import invalidate_geojson_cache, invalidate_observation_cache
from vespadb.observations.filters import ObservationFilter
from vespadb.observations.helpers import parse_and_convert_to_utc
from vespadb.observations.models import Municipality, Observation, Province, EradicationResultEnum
from vespadb.observations.serializers import (
    MunicipalitySerializer,
    ObservationSerializer,
    ProvinceSerializer,
)

if TYPE_CHECKING:
    from geopy.location import Location

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

BBOX_LENGTH = 4
GEOJSON_REDIS_CACHE_EXPIRATION = 900  # 15 minutes
GET_REDIS_CACHE_EXPIRATION = 86400  # 1 day
CSV_HEADERS = [
    "id", "created_datetime", "modified_datetime", "latitude", "longitude", "source", "source_id",
    "nest_height", "nest_size", "nest_location", "nest_type", "observation_datetime",
    "province", "eradication_date", "municipality", "images", "anb_domain",
    "notes", "eradication_result", "wn_id", "wn_validation_status", "nest_status"
]
BATCH_SIZE = 1000
class ExportError(Exception):
    """Custom exception for export-related errors."""
    pass

class QueryTimeoutError(Exception):
    """Custom exception for query timeout errors."""
    pass

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
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry_error_callback=lambda retry_state: None
    )
    def write_batch_to_file(
        self, 
        writer: Any,
        batch: List[Observation], 
        is_admin: bool, 
        user_municipality_ids: Set[str]
    ) -> int:
        """
        Write a batch of observations to the CSV file with retry logic.
        Returns number of successfully written records.
        """
        successful_writes = 0
        for observation in batch:
            try:
                row_data = self._prepare_row_data(observation, is_admin, user_municipality_ids)
                writer.writerow(row_data)
                successful_writes += 1
            except Exception as e:
                logger.error(f"Error processing observation {observation.id}: {str(e)}")
                continue
        return successful_writes

    def _prepare_row_data(
        self, 
        observation: Observation,
        is_admin: bool,
        user_municipality_ids: set[str]
    ) -> list[str]:
        """
        Prepare a single row of data for the CSV export with error handling.
        """
        try:
            # Determine allowed fields based on permissions
            if is_admin or (observation.municipality_id in user_municipality_ids):
                allowed_fields = user_read_fields
            else:
                allowed_fields = public_read_fields
                
            allowed_fields.extend(["source_id", "latitude", "longitude", "anb_domain", "nest_status"])
            
            row_data = []
            for field in CSV_HEADERS:
                try:
                    if field not in allowed_fields:
                        row_data.append("")
                        continue

                    if field == "latitude":
                        row_data.append(str(observation.location.y) if observation.location else "")
                    elif field == "longitude":
                        row_data.append(str(observation.location.x) if observation.location else "")
                    elif field in ["created_datetime", "modified_datetime", "observation_datetime"]:
                        datetime_val = getattr(observation, field, None)
                        if datetime_val:
                            datetime_val = datetime_val.replace(microsecond=0)
                            row_data.append(datetime_val.isoformat() + "Z")
                        else:
                            row_data.append("")
                    elif field == "province":
                        row_data.append(observation.province.name if observation.province else "")
                    elif field == "municipality":
                        row_data.append(observation.municipality.name if observation.municipality else "")
                    elif field == "anb_domain":
                        row_data.append(str(observation.anb))
                    elif field == "nest_status":
                        row_data.append(self.get_status(observation))
                    elif field == "source_id":
                        row_data.append(str(observation.source_id) if observation.source_id is not None else "")
                    else:
                        value = getattr(observation, field, "")
                        row_data.append(str(value) if value is not None else "")
                except Exception as e:
                    logger.warning(f"Error processing field {field} for observation {observation.id}: {str(e)}")
                    row_data.append("")
                    
            return row_data
        except Exception as e:
            logger.error(f"Error preparing row data for observation {observation.id}: {str(e)}")
            return [""] * len(CSV_HEADERS)  # Return empty row in case of error

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((OperationalError, psycopg2.OperationalError)),
        before=before_log(logger, logging.INFO),
        after=before_log(logger, logging.INFO)
    )
    def get_queryset_count(self, queryset: QuerySet) -> int:
        """Get queryset count with retry logic."""
        try:
            with transaction.atomic(), connection.cursor() as cursor:
                cursor.execute('SET statement_timeout TO 30000')  # 30 seconds timeout
                return int(queryset.count())
        except (OperationalError, psycopg2.OperationalError) as e:
            logger.error(f"Error getting queryset count: {str(e)}")
            raise QueryTimeoutError("Query timed out while getting count") from e

    def get_chunk_with_retries(
        self,
        queryset: QuerySet,
        start: int,
        batch_size: int,
        max_retries: int = 3
    ) -> Optional[List[Observation]]:
        """Get a chunk of data with retries and error handling."""
        for attempt in range(max_retries):
            try:
                with transaction.atomic(), connection.cursor() as cursor:
                    cursor.execute('SET statement_timeout TO 30000')
                    chunk = list(
                        queryset.select_related(
                            'province',
                            'municipality',
                            'reserved_by'
                        )[start:start + batch_size]
                    )
                    return chunk
            except (OperationalError, psycopg2.OperationalError) as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed to get chunk after {max_retries} attempts: {str(e)}")
                    return None
                wait_time = (2 ** attempt) * 1  # Exponential backoff
                logger.warning(f"Retry {attempt + 1}/{max_retries} after {wait_time}s")
                time.sleep(wait_time)
        return None

    def _generate_csv_content(
        self, 
        queryset: QuerySet,
        is_admin: bool,
        user_municipality_ids: Set[str]
    ) -> Generator[str, None, None]:
        """Generate CSV content in smaller chunks."""
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        
        # Write headers first
        writer.writerow(CSV_HEADERS)
        data = buffer.getvalue()
        buffer.seek(0)
        buffer.truncate()
        yield data

        # Process in smaller chunks
        chunk_size = 100  # Kleinere chunk size
        total = queryset.count()
        
        for start in range(0, total, chunk_size):
            chunk = queryset.select_related(
                'province', 
                'municipality', 
                'reserved_by'
            )[start:start + chunk_size]

            for observation in chunk:
                try:
                    row_data = self._prepare_row_data(
                        observation, 
                        is_admin, 
                        user_municipality_ids
                    )
                    writer.writerow(row_data)
                    data = buffer.getvalue()
                    buffer.seek(0)
                    buffer.truncate()
                    yield data
                except Exception as e:
                    logger.error(f"Error processing observation {observation.id}: {str(e)}")
                    continue

        buffer.close()
        
    def create_csv_generator(
        self,
        queryset: QuerySet,
        is_admin: bool,
        user_municipality_ids: Set[str],
        batch_size: int = BATCH_SIZE
    ) -> Generator[str, None, None]:
        """Create a generator for CSV streaming with improved error handling."""
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        
        # Write headers
        writer.writerow(CSV_HEADERS)
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)

        total_processed = 0
        successful_writes = 0
        error_count = 0
        
        try:
            total_count = self.get_queryset_count(queryset)
            
            # Process in chunks
            start = 0
            while True:
                chunk = self.get_chunk_with_retries(queryset, start, batch_size)
                if not chunk:
                    break
                    
                for observation in chunk:
                    try:
                        row_data = self._prepare_row_data(
                            observation,
                            is_admin,
                            user_municipality_ids
                        )
                        writer.writerow(row_data)
                        successful_writes += 1
                    except Exception as e:
                        error_count += 1
                        logger.error(f"Error processing observation {observation.id}: {str(e)}")
                        if error_count > total_count * 0.1:  # If more than 10% errors
                            raise ExportError("Too many errors during export")
                        continue
                    
                    data = buffer.getvalue()
                    yield data
                    buffer.seek(0)
                    buffer.truncate(0)
                
                total_processed += len(chunk)
                progress = (total_processed / total_count) * 100 if total_count else 0
                logger.info(
                    f"Export progress: {progress:.1f}% ({total_processed}/{total_count}). "
                    f"Successful: {successful_writes}, Errors: {error_count}"
                )
                
                start += batch_size
                
        except Exception as e:
            logger.exception("Error in CSV generator")
            raise ExportError(f"Export failed: {str(e)}") from e
        finally:
            buffer.close()

    @method_decorator(ratelimit(key="ip", rate="60/m", method="GET", block=True))
    @action(detail=False, methods=["get"], permission_classes=[AllowAny])
    def export(self, request: HttpRequest) -> StreamingHttpResponse:
        """
        Export observations as CSV using streaming response with improved error handling
        and performance optimizations.
        """
        try:
            # Validate export format
            if request.query_params.get("export_format", "csv").lower() != "csv":
                return JsonResponse({"error": "Only CSV export is supported"}, status=400)

            # Get user permissions
            if request.user.is_authenticated:
                user_municipality_ids = set(request.user.municipalities.values_list("id", flat=True))
                is_admin = request.user.is_superuser
            else:
                user_municipality_ids = set()
                is_admin = False

            # Get filtered queryset
            queryset = self.filter_queryset(self.get_queryset())
            
            # Create the StreamingHttpResponse
            response = StreamingHttpResponse(
                streaming_content=self._generate_csv_content(
                    queryset, is_admin, user_municipality_ids
                ),
                content_type='text/csv'
            )
            
            # Important headers
            filename = f"observations_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['X-Accel-Buffering'] = 'no'
            response['Cache-Control'] = 'no-cache'
            
            return response

        except Exception as e:
            logger.exception("Export failed")
            return JsonResponse(
                {"error": "Export failed. Please try again or contact support."}, 
                status=500
            )

    def get_status(self, observation: Observation) -> str:
        """Determine observation status based on eradication data."""
        logger.debug("Getting status for observation %s", observation.eradication_result)
        if observation.eradication_result:
            return "eradicated"
        if observation.reserved_by:
            return "reserved"
        return "untreated"

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
