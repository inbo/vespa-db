"""Filters for the Observation model."""

from rest_framework_gis.filterset import GeoFilterSet

from vespadb.observations.models import Observation


class ObservationFilter(GeoFilterSet):
    """Filter for the Observation model."""

    class Meta:
        """Meta class for the ObservationFilter."""

        model = Observation
        fields = ["reported_datetime", "validation_status"]
        geo_filters = {
            "location": ["exact", "distance_lte", "dwithin"],
        }
