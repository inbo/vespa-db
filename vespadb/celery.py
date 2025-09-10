"""Celery configuration file."""

import os

import django
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vespadb.settings")

django.setup()

from celery import Celery
app = Celery("vespadb")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
app.autodiscover_tasks(['vespadb.observations.tasks.generate_export'])
app.autodiscover_tasks(['vespadb.observations.tasks.generate_geojson_task'])
app.autodiscover_tasks(['vespadb.observations.tasks.generate_import'])
app.autodiscover_tasks(['vespadb.observations.tasks.observation_sync'])
app.autodiscover_tasks(['vespadb.observations.tasks.reservation_cleanup'])
