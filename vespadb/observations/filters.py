"""Filters for the Observation model."""

import django_filters
from django.db.models import QuerySet
from rest_framework_gis.filterset import GeoFilterSet

from vespadb.observations.models import Observation


class ListFilter(django_filters.BaseInFilter, django_filters.CharFilter):
    """Filter for a list of values."""


def filter_by_year_range(queryset: QuerySet[Observation], name: str, value: str) -> QuerySet[Observation]:
    """
    Filter the queryset by a list of years.

    It filters observations to those whose created_datetime falls within the specified years.

    Parameters
    ----------
    - queryset: The initial queryset to be filtered.
    - name: The name of the field being filtered.
    - value: A list of years (as strings or integers) to filter by.

    Returns
    -------
    - A filtered queryset including only those observations whose created_datetime
      falls within the specified years.
    """
    if not value:
        return queryset
    # Split the list into distinct years
    years = [int(year) for year in value.split(",")]
    # Filter queryset based on those years
    return queryset.filter(created_datetime__year__in=years)


class ObservationFilter(GeoFilterSet):
    """Filter for the Observation model."""

    municipality_id = ListFilter(field_name="municipality__id", lookup_expr="in")
    year_range = django_filters.CharFilter(method=filter_by_year_range)

    min_created_datetime = django_filters.DateTimeFilter(field_name="created_datetime", lookup_expr="gte")
    max_created_datetime = django_filters.DateTimeFilter(field_name="created_datetime", lookup_expr="lte")
    min_modified_datetime = django_filters.DateTimeFilter(field_name="modified_datetime", lookup_expr="gte")
    max_modified_datetime = django_filters.DateTimeFilter(field_name="modified_datetime", lookup_expr="lte")

    class Meta:
        """Meta class for the ObservationFilter."""

        model = Observation
        fields = [
            "municipality_id",
            "year_range",
            "min_created_datetime",
            "max_created_datetime",
            "min_modified_datetime",
            "max_modified_datetime",
        ]
        geo_filters = {
            "location": ["exact", "distance_lte", "dwithin"],
        }
