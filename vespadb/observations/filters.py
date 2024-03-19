"""Filters for the Observation model."""

import django_filters
from rest_framework_gis.filterset import GeoFilterSet

from vespadb.observations.models import Observation


class ObservationFilter(GeoFilterSet):
    """Filter for the Observation model."""

    min_creation_datetime = django_filters.DateTimeFilter(field_name="creation_datetime", lookup_expr="gte")
    max_creation_datetime = django_filters.DateTimeFilter(field_name="creation_datetime", lookup_expr="lte")
    min_modified_datetime = django_filters.DateTimeFilter(field_name="modified_datetime", lookup_expr="gte")
    max_modified_datetime = django_filters.DateTimeFilter(field_name="modified_datetime", lookup_expr="lte")

    class Meta:
        """Meta class for the ObservationFilter."""

        model = Observation
        fields = [
            "min_creation_datetime",
            "max_creation_datetime",
            "min_modified_datetime",
            "max_modified_datetime",
        ]
        geo_filters = {
            "location": ["exact", "distance_lte", "dwithin"],
        }
