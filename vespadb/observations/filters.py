"""Filters for the Observation model."""

import logging

import django_filters
from django.db.models import Q, QuerySet
from rest_framework_gis.filterset import GeoFilterSet

from vespadb.observations.models import Observation

logger = logging.getLogger(__name__)


class ListFilter(django_filters.BaseInFilter, django_filters.CharFilter):
    """Filter for a list of values."""


class MultiCharFilter(django_filters.BaseInFilter, django_filters.CharFilter):
    """Filter for handling multiple character inputs."""


class ObservationFilter(GeoFilterSet):
    """Filter for the Observation model."""

    municipality_id = ListFilter(field_name="municipality__id", lookup_expr="in")
    province_id = ListFilter(field_name="province__id", lookup_expr="in")

    min_created_datetime = django_filters.DateTimeFilter(field_name="created_datetime", lookup_expr="gte")
    max_created_datetime = django_filters.DateTimeFilter(field_name="created_datetime", lookup_expr="lte")
    min_modified_datetime = django_filters.DateTimeFilter(field_name="modified_datetime", lookup_expr="gte")
    max_modified_datetime = django_filters.DateTimeFilter(field_name="modified_datetime", lookup_expr="lte")
    min_observation_datetime = django_filters.DateTimeFilter(field_name="observation_datetime", lookup_expr="gte")
    max_observation_datetime = django_filters.DateTimeFilter(field_name="observation_datetime", lookup_expr="lte")
    anb = django_filters.BooleanFilter(field_name="anb")
    nest_type = MultiCharFilter(method="filter_nest_type")
    nest_status = MultiCharFilter(method="filter_nest_status")
    visible = django_filters.BooleanFilter(field_name="visible")

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

    class Meta:
        """Meta class for the ObservationFilter."""

        model = Observation
        fields = [
            "municipality_id",
            "province_id",
            "min_created_datetime",
            "max_created_datetime",
            "min_modified_datetime",
            "max_modified_datetime",
            "min_observation_datetime",
            "max_observation_datetime",
            "anb",
            "nest_type",
            "visible",
        ]
        geo_filters = {
            "location": ["exact", "distance_lte", "dwithin"],
        }
