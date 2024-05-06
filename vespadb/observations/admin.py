"""Observation app admin."""

from django.contrib import admin
from django.contrib.gis import admin as gis_admin
from vespadb.observations.models import Observation


class ObservationAdmin(gis_admin.GISModelAdmin):
    """Admin class for Observation model."""


admin.site.register(Observation, ObservationAdmin)
