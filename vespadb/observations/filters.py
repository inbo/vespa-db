"""Filters for the Observation model."""

import django_filters
from rest_framework_gis.filterset import GeoFilterSet

from vespadb.observations.models import Observation


class ObservationFilter(GeoFilterSet):
    """Filter for the Observation model."""

    min_creation_datetime = django_filters.DateTimeFilter(field_name="creation_datetime", lookup_expr="gte")
    max_creation_datetime = django_filters.DateTimeFilter(field_name="creation_datetime", lookup_expr="lte")
    min_last_modification_datetime = django_filters.DateTimeFilter(
        field_name="last_modification_datetime", lookup_expr="gte"
    )
    max_last_modification_datetime = django_filters.DateTimeFilter(
        field_name="last_modification_datetime", lookup_expr="lte"
    )

    class Meta:
        """Meta class for the ObservationFilter."""

        model = Observation
        fields = [
            "validation_status",
            "validated",
            "min_creation_datetime",
            "max_creation_datetime",
            "min_last_modification_datetime",
            "max_last_modification_datetime",
        ]
        geo_filters = {
            "location": ["exact", "distance_lte", "dwithin"],
        }
