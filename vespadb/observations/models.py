"""Observation models for the observations app."""

from django.contrib.gis.db import models as gis_models
from django.db import models
from django.db.models import JSONField


class Observation(models.Model):
    """Observation model for the observations app."""

    id = models.AutoField(primary_key=True)
    cluster = models.ForeignKey("Cluster", on_delete=models.CASCADE, related_name="observations", null=True, blank=True)
    external_id = models.CharField(max_length=255)
    creation_datetime = models.DateTimeField(auto_now_add=True)
    last_modification_datetime = models.DateTimeField(auto_now=True)

    # Observation details
    location = gis_models.PointField()
    source = models.CharField(max_length=255)
    validation_status = models.CharField(max_length=1)
    validated = models.BooleanField(default=False, blank=True)
    notes = models.TextField(null=True, blank=True)
    admin_notes = models.TextField(null=True, blank=True)
    species = models.IntegerField()
    activity = models.CharField(max_length=255)
    attributes = JSONField(default=list)
    images = JSONField(default=list)

    # Reporter details
    reporter_phone_number = models.CharField(max_length=20, blank=True, null=True)
    reporter_email = models.EmailField()
    reported_datetime = models.DateTimeField()


class Cluster(models.Model):
    """Cluster model for the observations app."""

    id = models.AutoField(primary_key=True)
    location = gis_models.PointField()
    species = models.IntegerField()
    admin_notes = models.TextField(null=True, blank=True)
    creation_datetime = models.DateTimeField(auto_now_add=True)
    last_modification_datetime = models.DateTimeField(auto_now=True)
