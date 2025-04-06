"""Serializers for the observations app."""

import logging
import re
import json
from datetime import UTC, datetime, date
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry, Point
from django.core.exceptions import PermissionDenied, ValidationError
from pytz import timezone
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework_gis.fields import GeometryField

from vespadb.observations.helpers import parse_and_convert_to_cet
from vespadb.observations.models import EradicationResultEnum, Municipality, Observation, Province, Export
from vespadb.observations.utils import get_municipality_from_coordinates
from vespadb.users.models import VespaUser

if TYPE_CHECKING:
    from rest_framework.request import Request

logger = logging.getLogger(__name__)

# Define which fields are returned for each permission level:
public_fields = [
    "id",
    "created_datetime",
    "modified_datetime",
    "location",
    "source",
    "source_id",
    "nest_height",
    "nest_size",
    "nest_location",
    "nest_type",
    "observation_datetime",
    "eradication_date",
    "municipality",
    "queen_present",
    "moth_present",
    "province",
    "images",
    "municipality_name",
    "notes",
    "eradication_result",
    "wn_id",
    "wn_validation_status",
    "anb",
    "visible",
    "wn_cluster_id",
    "nest_status",
    "duplicate_nest",
    "other_species_nest",
]

# Logged-in users WITH an assigned municipality see additional fields:
logged_in_fields = public_fields + [
    "public_domain",
    "reserved_by",
    "reserved_datetime",
    "reserved_by_first_name",
    "eradicator_name",
    "eradication_duration",
    "eradication_persons",
    "eradication_product",
    "eradication_method",
    "eradication_aftercare",
    "eradication_problems",
    "eradication_notes",
    "observer_phone_number",
    "observer_email",
    "observer_name",
]

# Admin users see extra fields (including fields that normally should be hidden from the public)
admin_fields = logged_in_fields + [
    "created_by",
    "modified_by",
    "created_by_first_name",
    "modified_by_first_name",
    "wn_modified_datetime",
    "wn_created_datetime",
    "admin_notes",
    "observer_received_email",
    "wn_admin_notes",
]

DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class ObservationSerializer(serializers.ModelSerializer):
    """Serializer for the full details of an Observation model instance."""

    municipality_name = serializers.CharField(source='municipality.name', read_only=True)
    nest_status = serializers.SerializerMethodField()
    location = GeometryField(required=False, allow_null=True)

    class Meta:
        """Meta class for the ObservationSerializer."""

        model = Observation
        fields = [
            'id', 'created_datetime', 'modified_datetime', 'location', 'source', 'source_id',
            'nest_height', 'nest_size', 'nest_location', 'nest_type', 'observation_datetime',
            'eradication_date', 'municipality', 'queen_present', 'moth_present', 'province',
            'images', 'municipality_name', 'notes', 'eradication_result', 'wn_id',
            'wn_validation_status', 'anb', 'visible', 'wn_cluster_id', 'nest_status',
            'reserved_by', 'reserved_datetime', 'eradicator_name', 'eradication_duration',
            'eradication_persons', 'eradication_product', 'eradication_method',
            'eradication_aftercare', 'eradication_problems', 'eradication_notes',
            'observer_phone_number', 'observer_email', 'observer_name', 'public_domain',
            'created_by', 'modified_by', 'wn_modified_datetime', 'wn_created_datetime',
            'admin_notes', 'observer_received_email', 'wn_admin_notes', "duplicate_nest", "other_species_nest"
        ]

        
    def get_municipality_name(self, obj: Observation) -> str | None:
        """Retrieve the name of the municipality associated with the observation, if any."""
        return obj.municipality.name if obj.municipality else None

    def get_nest_status(self, obj: Observation) -> str:  # Renamed method
        """Determine the status of the observation based on its properties."""
        if obj.eradication_result:
            return "eradicated"
        if obj.reserved_by:
            return "reserved"
        return "untreated"

    def get_reserved_by_first_name(self, obj: Observation) -> str | None:
        """Retrieve the first name of the user who reserved the observation."""
        return obj.reserved_by.first_name if obj.reserved_by else None

    def get_modified_by_first_name(self, obj: Observation) -> str | None:
        """Retrieve the first name of the user who modified the observation."""
        return obj.modified_by.first_name if obj.modified_by else None

    def get_created_by_first_name(self, obj: Observation) -> str | None:
        """Retrieve the first name of the user who created the observation."""
        return obj.created_by.first_name if obj.created_by else None
        
    def to_representation(self, instance: Observation) -> dict[str, Any]:
        """Dynamically filter fields based on user authentication status."""
        data = super().to_representation(instance)

        # Format datetime and date fields as required by frontend
        datetime_fields = [
            "created_datetime", "modified_datetime", "wn_modified_datetime",
            "wn_created_datetime", "reserved_datetime", "observation_datetime"
        ]
        date_fields = ["eradication_date"]

        for field in datetime_fields:
            if data.get(field):
                try:
                    dt = parse_and_convert_to_cet(data[field])
                    data[field] = dt.strftime("%Y-%m-%dT%H:%M:%S")
                except (ValueError, TypeError):
                    data[field] = None  # Fallback to None if parsing fails

        for field in date_fields:
            if data.get(field):
                try:
                    dt = datetime.strptime(data[field], "%Y-%m-%d")
                    data[field] = dt.strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    data[field] = None  # Fallback to None if parsing fails

        # Filter fields based on user permissions
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            if request.user.is_superuser:
                allowed = set(admin_fields)
            else:
                user_muni_ids = set(request.user.municipalities.values_list("id", flat=True))
                allowed = set(logged_in_fields if instance.municipality and instance.municipality.id in user_muni_ids else public_fields)
        else:
            allowed = set(public_fields)

        return {k: v for k, v in data.items() if k in allowed}

    def update(self, instance: Observation, validated_data: dict[Any, Any]) -> Observation:
        """Update method to handle observation updates."""
        user = self.context["request"].user

        # Non-admin users may only update observations in their assigned municipality.
        if not user.is_superuser:
            user_muni_ids = set(user.municipalities.values_list("id", flat=True))
            if instance.municipality and instance.municipality.id not in user_muni_ids:
                raise PermissionDenied("You do not have permission to update nests in this municipality.")

        # Prevent modification of wn_cluster_id (the cluster_id is public but not updatable)
        if "wn_cluster_id" in validated_data and validated_data["wn_cluster_id"] != instance.wn_cluster_id:
            raise serializers.ValidationError("wn_cluster_id cannot be updated.")

        # Automatically set modified_by to current user without needing to check permissions for this field
        validated_data['modified_by'] = user

        # For non-admins, disallow any admin-only fields from being updated.
        admin_update_fields = [
            "admin_notes",
            "observer_received_email",
            "wn_admin_notes",
            "visible",
            "created_by",
            "created_by_first_name",
            "modified_by_first_name",
        ]  # removed "modified_by" from this list
        if not user.is_superuser:
            for field in admin_update_fields:
                if field in validated_data:
                    raise serializers.ValidationError(f"Field {field} cannot be updated by non-admin users.")

        # Define which fields are allowed for update (separately for admin vs. non‑admin)
        allowed_update_fields_non_admin = [
            "location",
            "nest_height",
            "nest_size",
            "nest_location",
            "nest_type",
            "images",
            "reserved_by",
            "eradication_date",
            "eradicator_name",
            "eradication_duration",
            "eradication_persons",
            "eradication_result",
            "eradication_product",
            "eradication_method",
            "eradication_aftercare",
            "eradication_problems",
            "eradication_notes",
            "queen_present",
            "moth_present",
            "public_domain",
            "modified_by",  # explicitly allow modified_by for all users
            "duplicate_nest",
            "other_species_nest",
        ]
        
        # Define eradication-related fields
        eradication_related_fields = [
            "eradication_date",
            "eradicator_name",
            "eradication_duration",
            "eradication_persons",
            "eradication_method",
            "eradication_aftercare",
            "eradication_problems",
            "eradication_notes",
            "eradication_product",
        ]

        # Only check for eradication fields that have non-null values
        has_eradication_fields = any(
            field in validated_data 
            and validated_data[field] is not None 
            for field in eradication_related_fields
        )
        
        if has_eradication_fields and validated_data.get("eradication_result") is None:
            raise serializers.ValidationError(
                "Eradication result is required when providing eradication-related fields."
            )
            
        # Conditionally set `reserved_by` and `reserved_datetime`
        if "reserved_by" in validated_data:
            if validated_data["reserved_by"] is not None:
                validated_data["reserved_datetime"] = datetime.now(timezone("Europe/Brussels"))
            else:
                validated_data["reserved_datetime"] = None

        allowed_update_fields_admin = allowed_update_fields_non_admin + admin_update_fields
        allowed_update = set(allowed_update_fields_admin if user.is_superuser else allowed_update_fields_non_admin)
        
        # Remove any keys not in the allowed update set.
        for field in list(validated_data.keys()):
            if field not in allowed_update:
                validated_data.pop(field)
                
        instance = super().update(instance, validated_data)
        return instance
    
    def to_internal_value(self, data: dict[str, Any]) -> dict[str, Any]:
        """Convert the incoming data to a Python native representation."""
        # List of fields that should be parsed as datetime (with time)
        datetime_fields = [
            "created_datetime",
            "modified_datetime",
            "wn_modified_datetime",
            "wn_created_datetime",
            "reserved_datetime",
            "observation_datetime",
        ]
        # List of fields that should be treated as date only (no time)
        date_fields = ["eradication_date"]

        # Process datetime fields to ensure they are properly converted to UTC
        for field in datetime_fields + date_fields:
            if data.get(field):
                if isinstance(data[field], str):
                    try:
                        converted_datetime = parse_and_convert_to_cet(data[field])
                        if field in date_fields:
                            data[field] = converted_datetime.date()
                        else:
                            data[field] = converted_datetime
                    except (ValueError, TypeError) as err:
                        logger.exception(f"Invalid datetime format for {field}: {data[field]}")
                        raise serializers.ValidationError({
                            field: [f"Invalid datetime format for {field}."]
                        }).with_traceback(err.__traceback__) from None
                else:
                    data[field] = data[field]  # Already a valid datetime

        # Handle location validation separately (if provided)
        if "location" in data:
            data["location"] = self.validate_location(data["location"])
        data.pop("wn_admin_notes", None)
        internal_data = super().to_internal_value(data)
        return dict(internal_data)

    def validate_location(self, value: Any) -> Point:
        """Validate the input location data. Handle different formats of location data."""
        if value is None:
            return None

        if isinstance(value, Point):
            return value

        if isinstance(value, str):
            try:
                return GEOSGeometry(value, srid=4326)
            except (ValueError, TypeError) as e:
                raise serializers.ValidationError("Invalid WKT format for location.") from e

        elif isinstance(value, dict):
            # Check if it's GeoJSON format (with "type" and "coordinates")
            if "type" in value and "coordinates" in value:
                try:
                    # Convert dict to a JSON string so GEOSGeometry can parse it
                    return GEOSGeometry(json.dumps(value), srid=4326)
                except Exception as e:
                    raise serializers.ValidationError("Invalid GeoJSON format for location.") from e
            else:
                # Fallback: expect keys "latitude" and "longitude"
                latitude = value.get("latitude")
                longitude = value.get("longitude")
                if latitude is None or longitude is None:
                    raise serializers.ValidationError("Missing or invalid location data")
                return Point(float(longitude), float(latitude), srid=4326)

        raise serializers.ValidationError("Invalid location data type")

# Municipality serializers
class MunicipalitySerializer(serializers.ModelSerializer):
    """Serializer for the Municipality model."""

    class Meta:
        """Meta class for the MunicipalitySerializer."""

        model = Municipality
        fields = ["id", "name"]


class ProvinceSerializer(serializers.ModelSerializer):
    """Serializer for the Province model."""

    class Meta:
        """Meta class for the ProvinceSerializer."""

        model = Province
        fields = ["id", "name"]


class ExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Export
        fields = '__all__'
