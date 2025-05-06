"""Views for the observations app."""

import csv
import datetime
import io
import json
import time
import logging
import csv
import json
from typing import TYPE_CHECKING, Any, Union, List
from django.http import HttpResponseNotFound
import os
from typing import Iterator, Set
from django.db.models.query import QuerySet
from django.db.models import Model
from csv import writer as _writer
from django.db.models.query import QuerySet
from django.contrib.gis.geos import Point
from dateutil import parser

from django.views.decorators.csrf import csrf_exempt
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
from vespadb.observations.helpers import parse_and_convert_to_cet
from vespadb.observations.models import Municipality, Observation, Province, Export
from vespadb.observations.tasks.export_utils import generate_rows
from vespadb.observations.tasks.generate_export import generate_export
from vespadb.observations.serializers import ObservationSerializer, MunicipalitySerializer, ProvinceSerializer
from vespadb.observations.utils import check_if_point_in_anb_area, get_municipality_from_coordinates, get_geojson_cache_key
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from vespadb.observations.constants import MIN_OBSERVATION_DATETIME
from rest_framework.pagination import CursorPagination
from vespadb.observations.models import (
    NestHeightEnum, NestSizeEnum, NestLocationEnum, NestTypeEnum,
    EradicationResultEnum, EradicationProductEnum, EradicationMethodEnum,
    EradicationAfterCareEnum, EradicationProblemsEnum,
)
from vespadb.users.models import UserType
from vespadb.users.utils import get_import_user
if TYPE_CHECKING:
    from geopy.location import Location

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class Echo:
    """An object that implements just the write method of the file-like interface."""
    def write(self, value: Any) -> Any:
        """Write the value by returning it, instead of storing in a buffer."""
        return value


BBOX_LENGTH = 4
GEOJSON_REDIS_CACHE_EXPIRATION = 900  # 15 minutes
GET_REDIS_CACHE_EXPIRATION = 86400  # 1 day
BATCH_SIZE = 150

class ObservationCursorPagination(CursorPagination):
    page_size = 50
    ordering = ('observation_datetime', 'id')
    
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
    pagination_class = ObservationCursorPagination
    CHOICE_FIELDS = {
        'nest_height': NestHeightEnum,
        'nest_size': NestSizeEnum,
        'nest_location': NestLocationEnum,
        'nest_type': NestTypeEnum,
        'eradication_result': EradicationResultEnum,
        'eradication_product': EradicationProductEnum,
        'eradication_method': EradicationMethodEnum,
        'eradication_aftercare': EradicationAfterCareEnum,
        'eradication_problems': EradicationProblemsEnum,
    }

    def _validate_choice_fields(self, data_item: dict[str, Any]) -> str | None:
        """
        Ensure any incoming choice fields use a valid database value.
        Returns an error message if invalid, otherwise None.
        """
        for field, enum_cls in self.CHOICE_FIELDS.items():
            if field in data_item and data_item[field] is not None:
                val = data_item[field]
                valid_values = [choice[0] for choice in enum_cls.choices]
                if val not in valid_values:
                    return (
                        f"Invalid value for '{field}': '{val}'. "
                        f"Allowed values are: {', '.join(valid_values)}."
                    )
        return None
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

    def get_permissions(self) -> List[BasePermission]:
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
        base_queryset = super().get_queryset().select_related('municipality', 'province')
    
        # Add default filter for visible observations
        visible_param = self.request.query_params.get("visible", "true")
        if visible_param.lower() != "all" and (not self.request.user.is_authenticated or not self.request.user.is_superuser):
            base_queryset = base_queryset.filter(visible=True)
        
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
                        data[field] = parse_and_convert_to_cet(value).isoformat()
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

    @method_decorator(ratelimit(key="ip", rate="60/m", method="GET", block=True))
    @swagger_auto_schema(
        operation_description="Retrieve a list of observations. Supports filtering and ordering.",
        responses={200: ObservationSerializer(many=True)},
    )
    def retrieve_list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Handle requests for the list of observations with pagination and caching.
        """
        query_params = request.GET.copy()
        cursor = query_params.get('cursor', '')
        cache_key = f"observations_list:{hash(str(query_params))}:cursor_{cursor}"

        # Check cache
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            cache.set(cache_key, response.data, timeout=3600)  # Cache for 1 hour
            return response

        # In case pagination is disabled (should not happen)
        serializer = self.get_serializer(queryset, many=True)
        response_data = {"results": serializer.data}
        cache.set(cache_key, response_data, timeout=3600)
        return Response(response_data)
    
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
            
            # Set default visible=true if not specified and not an admin
            if 'visible' not in query_params and (not request.user.is_authenticated or not request.user.is_superuser):
                query_params['visible'] = 'true'
                
            if 'min_observation_datetime' not in query_params:
                query_params['min_observation_datetime'] = MIN_OBSERVATION_DATETIME

            cache_key = get_geojson_cache_key(query_params)
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.info(f"Returning cached GeoJSON data, found cache: {cache_key}")
                return JsonResponse(cached_data, safe=False)
            
            # Rest of your view logic remains the same
            bbox = None
            if bbox_str:
                bbox_coords = list(map(float, bbox_str.split(",")))
                if len(bbox_coords) == BBOX_LENGTH:
                    xmin, ymin, xmax, ymax = bbox_coords
                    bbox_wkt = f"POLYGON(({xmin} {ymin}, {xmin} {ymax}, {xmax} {ymax}, {xmax} {ymin}, {xmin} {ymin}))"
                    bbox = GEOSGeometry(bbox_wkt, srid=4326)
                else:
                    return HttpResponse("Invalid bbox format", status=400)

            queryset = self.filter_queryset(
                self.get_queryset().select_related('municipality')
            ).annotate(point=Transform("location", 4326))
            if bbox:
                queryset = queryset.filter(location__within=bbox)

            def generate_features(qs):
                for obs in qs.iterator(chunk_size=1000):
                    yield {
                        "type": "Feature",
                        "properties": {
                            "id": obs.id,
                            "status": "eradicated" if obs.eradication_result else "reserved" if obs.reserved_by else "default",
                        },
                        "geometry": json.loads(obs.point.geojson) if obs.point else None,
                    }

            features = list(generate_features(queryset))
            geojson_response = {"type": "FeatureCollection", "features": features}
            logger.info(f"Generating GeoJSON in view with cache_key {cache_key}")
            cache.set(cache_key, geojson_response, GEOJSON_REDIS_CACHE_EXPIRATION)
            return JsonResponse(geojson_response, safe=False)
        except Exception as e:
            logger.exception("GeoJSON generation failed")
            return HttpResponse("Error generating GeoJSON", status=500)
            
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

        # Set the request user to the import user
        import_user = get_import_user(UserType.IMPORT)
        request.user = import_user

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
                            row[field] = parse_and_convert_to_cet(row[field])
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
                    point_str = location.split(";")[1].strip()
                    geom = GEOSGeometry(point_str, srid=4326)
                else:
                    geom = GEOSGeometry(location, srid=4326)
                logger.info(f"Validated GEOSGeometry: {geom}")
                return geom
            raise ValidationError("Invalid location data type")
        except (ValueError, TypeError) as e:
            logger.exception(f"Invalid location data: {location} - {e}")
            raise ValidationError("Invalid WKT format for location.") from e
    
    def parse_boolean(self, value):
        """Convert string boolean values to Python boolean."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            value = value.lower().strip()
            if value == 'true':
                return True
            elif value == 'false':
                return False
        return None

    def process_data(self, data: List[dict[str, Any]]) -> tuple[List[Observation], List[dict[str, Any]]]:
        """Process and validate the incoming data, splitting between updates and new records."""
        logger.info("Starting to process import data")
        
        valid_observations: List[Union[dict[str, Any], Observation]] = []
        errors = []
        current_time = now()
        
        # Define the allowed fields for import
        allowed_fields = {
            'id', 'source_id', 'observation_datetime', 'eradication_problems',
            'source', 'eradication_notes', 'images', 'created_datetime',
            'longitude', 'latitude', 'eradication_persons', 'nest_size',
            'visible', 'nest_location', 'eradication_date', 'eradication_product',
            'nest_type', 'eradicator_name', 'eradication_method',
            'eradication_aftercare', 'public_domain', 'eradication_duration',
            'nest_height', 'eradication_result', 'notes', 'admin_notes',
            'queen_present', 'moth_present', 'duplicate_nest', 'other_species_nest',
        }
        
        # Fields that need boolean conversion
        boolean_fields = {'visible', 'public_domain', 'queen_present', 'moth_present', 'duplicate_nest', 'other_species_nest'}
        
        for idx, data_item in enumerate(data, start=1):
            # Only allow specific fields
            data_item = {k: v for k, v in data_item.items() if k in allowed_fields}
            
            # Process boolean fields
            for field in boolean_fields:
                if field in data_item:
                    data_item[field] = self.parse_boolean(data_item[field])
            
            # If an id is provided, treat as update; otherwise as create.
            if "id" in data_item and data_item["id"]:
                result = self.process_update_item(data_item, idx, current_time)
            else:
                result = self.process_create_item(data_item, idx, current_time)
                
            if isinstance(result, dict) and result.get("error"):
                errors.append({"record": idx, "error": result["error"]})
            elif result is not None:  # Only add if not None
                valid_observations.append(result)
            else:
                logger.warning(f"Unexpected None result for record {idx}")
                errors.append({"record": idx, "error": "Unexpected None result"})                
        return valid_observations, errors
        
    def process_update_item(self, data_item: dict[str, Any], idx: int, current_time: datetime.datetime) -> Any:
        """
        Process a single record as an update.
        
        In update mode, we only require an "id" plus any fields that should be updated.
        For example, if only eradication_result is provided, observation_datetime is not mandatory.
        """
        if err := self._validate_choice_fields(data_item):
            return {"error": f"Record {idx}: {err}"}
        
        observation_id = data_item.get("id")
        try:
            # First attempt to find by exact ID
            existing_obj = Observation.objects.get(id=observation_id)
            logger.info(f"Found existing observation #{observation_id} for update")
        except Observation.DoesNotExist:
            logger.warning(f"Observation with id {observation_id} not found, falling back to create for record {idx}")
            return self.process_create_item(data_item, idx, current_time)
        
        # Get the import user
        import_user = get_import_user(UserType.IMPORT)
        
        # Set the update audit fields
        data_item['modified_by'] = import_user
        data_item['modified_datetime'] = current_time

        # Remove created_by and created_datetime to prevent modification
        data_item.pop('created_by', None)
        data_item.pop('created_datetime', None)

        # Process datetime fields
        datetime_fields = [
            "modified_datetime",
            "observation_datetime",
            "wn_modified_datetime",
            "wn_created_datetime",
            "reserved_datetime"
        ]
        
        for field in datetime_fields:
            if field in data_item and data_item[field]:
                try:
                    dt_value = parse_and_convert_to_cet(data_item[field])
                    data_item[field] = dt_value
                    logger.info(f"Parsed {field} for record {idx}: {dt_value}")
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid datetime format for {field} in record {idx}: {data_item[field]} - {e}")
                    data_item[field] = None

        # If coordinates are provided, update the location, municipality, province, and ANB flag
        if 'longitude' in data_item and 'latitude' in data_item:
            try:
                long_val = float(data_item.pop('longitude'))
                lat_val = float(data_item.pop('latitude'))
                data_item['location'] = Point(long_val, lat_val, srid=4326)
                municipality = get_municipality_from_coordinates(long_val, lat_val)
                if municipality:
                    data_item['municipality'] = municipality
                    if municipality.province:
                        data_item['province'] = municipality.province
                
                # Always explicitly update ANB status when coordinates change
                data_item['anb'] = check_if_point_in_anb_area(long_val, lat_val)
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid coordinates for record {idx}: {str(e)}")
                return {"error": f"Invalid coordinates: {str(e)}"}
        
        data_item['id'] = observation_id
        return data_item
    
    def process_create_item(self, data_item: dict[str, Any], idx: int, current_time: datetime.datetime) -> Any:
        """
        Process a single record as a new observation.
        
        In create mode, observation_datetime, latitude and longitude are required.
        """
        if err := self._validate_choice_fields(data_item):
            return {"error": f"Record {idx}: {err}"}
        
        # Check if ID is specified
        observation_id = data_item.get("id")
        
        # Ensure required fields for a new record are present
        required_fields = ["observation_datetime", "longitude", "latitude"]
        missing_fields = [field for field in required_fields if not data_item.get(field)]
        if missing_fields:
            return {"error": f"Missing required fields for new record: {', '.join(missing_fields)}"}
        
        # Get the import user
        import_user = get_import_user(UserType.IMPORT)
        
        # Store original created_datetime if provided
        original_created_datetime = data_item.get('created_datetime')
        logger.info(f"Processing created_datetime for record {idx}: {original_created_datetime} (type: {type(original_created_datetime)})")
        
        # Set audit fields
        data_item['created_by'] = import_user
        data_item['modified_by'] = import_user
        data_item['modified_datetime'] = current_time
        
        # Process created_datetime
        if original_created_datetime:
            try:
                if not isinstance(original_created_datetime, str):
                    logger.warning(f"created_datetime is not a string: {original_created_datetime}")
                    raise ValueError("created_datetime must be a string")
                parsed_dt = parse_and_convert_to_cet(original_created_datetime)
                data_item['created_datetime'] = parsed_dt
                logger.info(f"Parsed created_datetime for record {idx}: {parsed_dt}")
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid datetime format for created_datetime in record {idx}: {original_created_datetime} - {e}")
                data_item['created_datetime'] = current_time
                logger.info(f"Falling back to current time for created_datetime in record {idx}: {current_time}")
        else:
            data_item['created_datetime'] = current_time
            logger.info(f"No created_datetime provided for record {idx}, using current time: {current_time}")

        # Process other datetime fields
        datetime_fields = [
            "modified_datetime",
            "observation_datetime",
            "wn_modified_datetime",
            "wn_created_datetime",
            "reserved_datetime"
        ]
        
        for field in datetime_fields:
            if field in data_item and data_item[field]:
                try:
                    dt_value = parse_and_convert_to_cet(data_item[field])
                    data_item[field] = dt_value
                    logger.info(f"Parsed {field} for record {idx}: {dt_value}")
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid datetime format for {field} in record {idx}: {data_item[field]} - {e}")
                    if field == "observation_datetime":  # This is required
                        return {"error": f"Invalid datetime format for required field {field}: {data_item[field]}"}
                    data_item[field] = None
        
        try:
            long_val = float(data_item.pop('longitude'))
            lat_val = float(data_item.pop('latitude'))
            data_item['location'] = Point(long_val, lat_val, srid=4326)
            logger.info(f"Created point from coordinates for record {idx}: {long_val}, {lat_val}")
            
            municipality = get_municipality_from_coordinates(long_val, lat_val)
            if municipality:
                data_item['municipality'] = municipality
                if municipality.province:
                    data_item['province'] = municipality.province
            
            # Always explicitly set ANB status
            data_item['anb'] = check_if_point_in_anb_area(long_val, lat_val)            
            return data_item  # Return the processed dictionary
        except (ValueError, TypeError) as e:
            logger.error(f"Error processing coordinates for record {idx}: {str(e)}")
            return {"error": f"Invalid coordinates: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error in process_create_item for record {idx}: {str(e)}")
            return {"error": f"Unexpected error: {str(e)}"}
    
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
                # Keep ISO format strings as-is
                if isinstance(data_dict[field], str):
                    try:
                        # Just validate the format but keep original value
                        parser.parse(data_dict[field])
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

        cleaned_data = {k: v for k, v in data_dict.items() if v not in [None, ""]}
        logger.info("Cleaned data item: %s", cleaned_data)
        return cleaned_data

    def save_observations(self, valid_data: list[Union[dict[str, Any], Observation]]) -> Response:
        """Save the valid observations to the database."""
        try:
            logger.info(f"Saving {len(valid_data)} valid observations")
            created_ids: list[int] = []
            updated_ids: list[int] = []

            with transaction.atomic():
                for data in valid_data:
                    if isinstance(data, Observation):
                        data.save()
                        created_ids.append(data.id)
                        continue

                    observation_id = data.pop('id', None)
                    logger.info(f"Processing data for observation_id={observation_id}: {data}")  # Add logging
                    if observation_id:
                        try:
                            obs = Observation.objects.get(id=observation_id)
                            for field, value in data.items():
                                setattr(obs, field, value)
                            obs.save()
                            updated_ids.append(obs.id)
                            logger.info(f"Updated observation #{obs.id}")
                        except Observation.DoesNotExist:
                            data['id'] = observation_id
                            obs = Observation.objects.create(**data)
                            created_ids.append(obs.id)
                            logger.info(f"Created new observation #{obs.id}")
                    else:
                        obs = Observation.objects.create(**data)
                        created_ids.append(obs.id)
                        logger.info(f"Created new observation #{obs.id}")

            invalidate_geojson_cache()

            parts: list[str] = []
            if created_ids:
                c = len(created_ids)
                parts.append(f"{c} new record{'s' if c != 1 else ''} created")
            if updated_ids:
                c = len(updated_ids)
                parts.append(f"{c} existing record{'s' if c != 1 else ''} updated")
            summary = "; ".join(parts) or "No changes made"

            return Response(
                {
                    "message": summary + ".",
                    "created_ids": created_ids,
                    "updated_ids": updated_ids,
                },
                status=status.HTTP_201_CREATED
            )
        except IntegrityError as e:
            logger.exception("Error during bulk import")
            return Response(
                {"error": f"An error occurred during bulk import: {e!s}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
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

    @method_decorator(csrf_exempt)
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def export_direct(self, request: HttpRequest) -> Union[StreamingHttpResponse, JsonResponse]:
        """Stream observations directly as CSV with optimized memory usage."""
        try:
            # Initialize the filterset with request parameters
            filterset = self.filterset_class(
                data=request.GET,
                queryset=self.get_queryset().select_related(
                    'province', 
                    'municipality'
                )
            )

            if not filterset.is_valid():
                return JsonResponse({"error": filterset.errors}, status=400)

            # Get filtered queryset
            queryset = filterset.qs

            # Check count with a more efficient query
            total_count = queryset.count()
            if total_count > 10000:
                return JsonResponse({
                    "error": f"Export too large. Found {total_count} records, maximum allowed is 10,000"
                }, status=400)

            # Determine user permissions
            is_admin = request.user.is_authenticated and request.user.is_superuser
            user_municipality_ids = set()
            if request.user.is_authenticated:
                user_municipality_ids = set(
                    request.user.municipalities.values_list('id', flat=True)
                )

            # Create the streaming response
            pseudo_buffer = Echo()
            writer = csv.writer(pseudo_buffer)
            response = StreamingHttpResponse(
                streaming_content=generate_rows(
                    queryset=queryset,
                    writer=writer,
                    is_admin=is_admin,
                    user_municipality_ids=user_municipality_ids,
                    batch_size=200  # Smaller batch size for memory efficiency
                ),
                content_type='text/csv'
            )
            # Set filename with timestamp
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            response['Content-Disposition'] = f'attachment; filename="observations_export_{timestamp}.csv"'
            # Add CORS headers
            response["Access-Control-Allow-Origin"] = request.META.get('HTTP_ORIGIN', '*')
            response["Access-Control-Allow-Credentials"] = "true"
            response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            return response

        except Exception as e:
            logger.exception("Export failed")
            return JsonResponse({"error": str(e)}, status=500)
        
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

    def get_permissions(self) -> List[BasePermission]:
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

    def get_permissions(self) -> List[BasePermission]:
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
