"""Filters for the Observation model."""

import logging
from typing import Any

import django_filters
from django.contrib.admin import SimpleListFilter
from django.db.models import Q, QuerySet
from django.utils.translation import gettext_lazy as _
from rest_framework_gis.filterset import GeoFilterSet

from vespadb.observations.models import Municipality, Observation, Province

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
            query |= Q(eradication_date__isnull=False)
        if "reserved" in value:
            query |= Q(reserved_datetime__isnull=False)
        if "open" in value:
            query |= Q(reserved_datetime__isnull=True, eradication_date__isnull=True)

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


class ProvinceFilter(SimpleListFilter):
    """Custom filter for selecting provinces in the admin panel."""

    title: str = _("province")
    parameter_name: str = "province"

    def lookups(self, request: Any, model_admin: Any) -> list[tuple[int, str]]:
        """
        Return a list of tuples for the provinces to be used in the filter dropdown.

        Args:
            request (Any): The HTTP request object.
            model_admin (Any): The admin model object.

        Returns
        -------
            List[Tuple[int, str]]: List of province id and name tuples.
        """
        provinces = Province.objects.all()
        return [(province.id, province.name) for province in provinces]

    def queryset(self, request: Any, queryset: QuerySet) -> QuerySet | None:
        """
        Filter the queryset based on the selected province.

        Args:
            request (Any): The HTTP request object.
            queryset (QuerySet): The initial queryset to be filtered.

        Returns
        -------
            Optional[QuerySet]: The filtered queryset based on the selected province, or the original queryset if no province is selected.
        """
        if self.value():
            return queryset.filter(province_id=self.value())
        return queryset


class MunicipalityExcludeFilter(SimpleListFilter):
    """Custom filter for excluding a specific municipality in the admin panel."""

    title: str = _("exclude municipality")
    parameter_name: str = "municipality__exclude"

    def lookups(self, request: Any, model_admin: Any) -> list[tuple[int, str]]:
        """
        Return a list of tuples for the municipalities to be used in the filter dropdown.

        Args:
            request (Any): The HTTP request object.
            model_admin (Any): The admin model object.

        Returns
        -------
            List[Tuple[int, str]]: List of municipality id and name tuples.
        """
        municipalities = Municipality.objects.all()
        return [(municipality.id, municipality.name) for municipality in municipalities]

    def queryset(self, request: Any, queryset: QuerySet) -> QuerySet | None:
        """
        Filter the queryset to exclude the selected municipality.

        Args:
            request (Any): The HTTP request object.
            queryset (QuerySet): The initial queryset to be filtered.

        Returns
        -------
            Optional[QuerySet]: The filtered queryset with the selected municipality excluded, or the original queryset if no municipality is selected.
        """
        if self.value():
            return queryset.exclude(municipality_id=self.value())
        return queryset
