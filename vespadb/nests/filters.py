"""Filters for the Nest model."""

from django.contrib.gis.db import models
from rest_framework_gis.filterset import GeoFilterSet

from vespadb.nests.models import Nest


class NestFilter(GeoFilterSet):
    """Filter for the Nest model."""

    class Meta:
        """Meta class for the NestFilter."""

        model = Nest
        fields = ["reported_datetime", "status", "nature_reserve", "public_domain"]
        geo_filters = {
            "location": ["exact", "distance_lte", "dwithin"],
        }
