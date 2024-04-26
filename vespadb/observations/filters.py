"""Filters for the Observation model."""

import django_filters
from django.db.models import QuerySet
from rest_framework_gis.filterset import GeoFilterSet

from vespadb.observations.models import Observation
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)

class ListFilter(django_filters.BaseInFilter, django_filters.CharFilter):
    """Filter for a list of values."""

class MultiCharFilter(django_filters.BaseInFilter, django_filters.CharFilter):
    """Filter for handling multiple character inputs."""
    pass

class ObservationFilter(GeoFilterSet):
    """Filter for the Observation model."""

    municipality_id = ListFilter(field_name="municipality__id", lookup_expr="in")
    province_id = ListFilter(field_name="province__id", lookup_expr="in")
    year_range = django_filters.CharFilter(method="filter_by_year_range")

    min_created_datetime = django_filters.DateTimeFilter(field_name="created_datetime", lookup_expr="gte")
    max_created_datetime = django_filters.DateTimeFilter(field_name="created_datetime", lookup_expr="lte")
    min_modified_datetime = django_filters.DateTimeFilter(field_name="modified_datetime", lookup_expr="gte")
    max_modified_datetime = django_filters.DateTimeFilter(field_name="modified_datetime", lookup_expr="lte")
    anb = django_filters.BooleanFilter(field_name="anb")
    nest_type = MultiCharFilter(method="filter_nest_type")
    nest_status = MultiCharFilter(method="filter_nest_status")

    def filter_nest_status(self, queryset: QuerySet, name: str, value: str) -> QuerySet:
        """
        Filter the queryset based on multiple nest statuses.

        Parameters
        ----------
        queryset : QuerySet
            The initial queryset to be filtered.
        name : str
            The name of the filter being applied.
        value : list
            A list of desired nest statuses to filter by (e.g., ['eradicated', 'reserved']).

        Returns
        -------
        QuerySet
            The filtered queryset based on the provided nest statuses.
        """
        if not value:
            return queryset
        query = Q()
        if "eradicated" in value:
            query |= Q(eradication_datetime__isnull=False)
        if "reserved" in value:
            query |= Q(reserved_datetime__isnull=False)
        if "open" in value:
            query |= Q(reserved_datetime__isnull=True, eradication_datetime__isnull=True)

        return queryset.filter(query)
    def filter_nest_type(self, queryset: QuerySet, name: str, value: str) -> QuerySet:
        """
        Filter the queryset based on multiple nest types.

        Parameters
        ----------
        queryset : QuerySet
            The initial queryset to be filtered.
        name : str
            The name of the filter being applied.
        value : list
            A list of desired nest types to filter by (e.g., ['active_embryonal_nest', 'inactive_empty_nest']).

        Returns
        -------
        QuerySet
            The filtered queryset based on the provided nest types.
        """
        if not value:
            return queryset
        return queryset.filter(nest_type__in=value)
    
    def filter_by_year_range(self, queryset: QuerySet[Observation], name: str, value: str) -> QuerySet[Observation]:
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

    class Meta:
        """Meta class for the ObservationFilter."""

        model = Observation
        fields = [
            "municipality_id",
            "province_id",
            "year_range",
            "min_created_datetime",
            "max_created_datetime",
            "min_modified_datetime",
            "max_modified_datetime",
            "anb",
            "nest_type",
        ]
        geo_filters = {
            "location": ["exact", "distance_lte", "dwithin"],
        }
