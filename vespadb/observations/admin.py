"""Vespawatch admin."""

from django.contrib.gis import admin

from vespadb.observations.models import Observation

admin.site.register(Observation, admin.GISModelAdmin)
