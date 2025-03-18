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

from vespadb.observations.helpers import parse_and_convert_to_cet, parse_and_convert_to_cet
from vespadb.observations.models import EradicationResultEnum, Municipality, Observation, Province, Export
from vespadb.observations.utils import get_municipality_from_coordinates
from vespadb.users.models import VespaUser

if TYPE_CHECKING:
    from rest_framework.request import Request

logger = logging.getLogger(__name__)
DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")

class ObservationSerializer(serializers.ModelSerializer):
    municipality_name = serializers.SerializerMethodField()
    nest_status = serializers.SerializerMethodField()
    reserved_by_first_name = serializers.SerializerMethodField()
    modified_by_first_name = serializers.SerializerMethodField()
    created_by_first_name = serializers.SerializerMethodField()
    eradication_date = serializers.DateField(
        required=False, allow_null=True, format="%Y-%m-%d", input_formats=["%Y-%m-%d"]
    )
    location = GeometryField(required=False, allow_null=True)

    class Meta:
        model = Observation
        fields = "__all__"

    def get_municipality_name(self, obj: Observation) -> str | None:
        return obj.municipality.name if obj.municipality else None

    def get_nest_status(self, obj: Observation) -> str:
        if obj.eradication_result:
            return "eradicated"
        if obj.reserved_by:
            return "reserved"
        return "untreated"

    def get_reserved_by_first_name(self, obj: Observation) -> str | None:
        return obj.reserved_by.first_name if obj.reserved_by else None

    def get_modified_by_first_name(self, obj: Observation) -> str | None:
        return obj.modified_by.first_name if obj.modified_by else None

    def get_created_by_first_name(self, obj: Observation) -> str | None:
        return obj.created_by.first_name if obj.created_by else None

    def to_representation(self, instance: Observation) -> dict[str, any]:
        data: dict[str, any] = super().to_representation(instance)
        # Rename "status" to "nest_status" for the output
        if "status" in data:
            data["nest_status"] = data.pop("status")

        # Convert datetime fields as needed (using your helper to CET)
        datetime_fields = [
            "created_datetime",
            "modified_datetime",
            "wn_modified_datetime",
            "wn_created_datetime",
            "reserved_datetime",
            "observation_datetime",
        ]
        date_fields = ["eradication_date"]

        for field in datetime_fields:
            if data.get(field):
                dt = parse_and_convert_to_cet(data[field])
                data[field] = dt.strftime("%Y-%m-%dT%H:%M:%S")
        for field in date_fields:
            if data.get(field):
                date_str: str = data[field]
                try:
                    parsed_date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=UTC)
                    data[field] = parsed_date.strftime("%Y-%m-%d")
                except ValueError:
                    try:
                        parsed_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=UTC)
                        data[field] = parsed_date.strftime("%Y-%m-%d")
                    except Exception:
                        pass

        # Define which fields are returned for each permission level:
        public_fields = [
            "id",
            "created_datetime",
            "modified_datetime",
            "location",
            "source",
            "source_id",
            "nest_status",
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
        ]
        # Logged-in users WITH an assigned municipality see one extra field:
        logged_in_fields = public_fields + ["public_domain"]
        # Admin users see extra fields (including fields that normally should be hidden from the public)
        admin_fields = public_fields + [
            "public_domain",
            "visible",
            "created_by",
            "modified_by",
            "created_by_first_name",
            "modified_by_first_name",
            "admin_notes",
            "observer_received_email",
        ]

        request = self.context.get("request")
        if request and request.user.is_authenticated:
            user = request.user
            if user.is_superuser:
                allowed = admin_fields
            else:
                # Check if the observation’s municipality is one of the user’s assigned ones
                user_muni_ids = set(user.municipalities.values_list("id", flat=True))
                if instance.municipality and instance.municipality.id in user_muni_ids:
                    allowed = logged_in_fields
                else:
                    allowed = public_fields
        else:
            allowed = public_fields

        return {field: data[field] for field in allowed if field in data}

    def update(self, instance: Observation, validated_data: dict[str, any]) -> Observation:
        user = self.context["request"].user

        # Non-admin users may only update observations in their assigned municipality.
        if not user.is_superuser:
            user_muni_ids = set(user.municipalities.values_list("id", flat=True))
            if instance.municipality and instance.municipality.id not in user_muni_ids:
                raise PermissionDenied("You do not have permission to update nests in this municipality.")

        # Prevent modification of wn_cluster_id (the cluster_id is public but not updatable)
        if "wn_cluster_id" in validated_data and validated_data["wn_cluster_id"] != instance.wn_cluster_id:
            raise serializers.ValidationError("wn_cluster_id cannot be updated.")

        # For non-admins, disallow any admin-only fields from being updated.
        admin_update_fields = [
            "admin_notes",
            "observer_received_email",
            "wn_admin_notes",
            "visible",
            "created_by",
            "modified_by",
            "created_by_first_name",
            "modified_by_first_name",
        ]
        if not user.is_superuser:
            for field in admin_update_fields:
                if field in validated_data:
                    raise serializers.ValidationError(f"Field {field} cannot be updated by non-admin users.")

        # Now define which fields are allowed for update (separately for admin vs. non‑admin)
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
        ]
        allowed_update_fields_admin = allowed_update_fields_non_admin + admin_update_fields

        allowed_update = set(allowed_update_fields_admin if user.is_superuser else allowed_update_fields_non_admin)
        # Remove any keys not in the allowed update set.
        for field in list(validated_data.keys()):
            if field not in allowed_update:
                validated_data.pop(field)
        instance = super().update(instance, validated_data)
        return instance

    def to_internal_value(self, data: dict[str, any]) -> dict[str, any]:
        logger.info("Raw input data: %s", data)
        datetime_fields = [
            "created_datetime",
            "modified_datetime",
            "wn_modified_datetime",
            "wn_created_datetime",
            "reserved_datetime",
            "observation_datetime",
        ]
        date_fields = ["eradication_date"]

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

        if "location" in data:
            data["location"] = self.validate_location(data["location"])
        data.pop("wn_admin_notes", None)
        internal_data = super().to_internal_value(data)
        return dict(internal_data)

    def validate_location(self, value: any) -> Point:
        if value is None:
            return None

        if isinstance(value, Point):
            return value

        if isinstance(value, str):
            try:
                return GEOSGeometry(value, srid=4326)
            except (ValueError, TypeError) as e:
                raise serializers.ValidationError("Invalid WKT format for location.") from e

        if isinstance(value, dict):
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
