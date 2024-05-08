"""Observation app admin."""

from django.contrib import admin
from django.contrib.gis import admin as gis_admin

from vespadb.observations.models import (
    Observation,
)


class ObservationAdmin(gis_admin.GISModelAdmin):
    """Admin class for Observation model."""

    list_display = (
        "id",
        "observation_datetime",
        "eradication_datetime",
        "eradicator_name",
        "wn_validation_status",
        "nest_height",
        "nest_size",
        "nest_location",
        "nest_type",
        "eradication_result",
        "municipality",
        "province",
        "reserved_by",
        "created_by",
        "modified_by",
    )
    list_filter = (
        "observation_datetime",
        "eradication_datetime",
        "eradicator_name",
        "wn_validation_status",
        "nest_height",
        "nest_size",
        "nest_location",
        "nest_type",
        "eradication_result",
        "municipality",
        "province",
        "reserved_by",
        "created_by",
        "modified_by",
    )
    search_fields = ("id", "eradicator_name", "observer_name")
    filter_horizontal = ()
    ordering = ("-observation_datetime",)
    raw_id_fields = ("municipality", "province")


admin.site.register(Observation, ObservationAdmin)
