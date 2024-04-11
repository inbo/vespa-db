"""Celery configuration file."""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vespadb.settings")

app = Celery("vespadb")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
