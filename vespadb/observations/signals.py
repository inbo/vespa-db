"""Signals for observations."""

from typing import Any

from django.db.models.base import ModelBase
from django.db.models.signals import post_delete
from django.dispatch import receiver

from vespadb.observations.models import Observation


@receiver(post_delete, sender=Observation)
def delete_cluster_if_empty(sender: ModelBase, instance: Observation, **kwargs: Any) -> None:
    """Delete the cluster if it has no observations."""
    # Only delete a cluster if it has no observations
    if not Observation.objects.filter(cluster=instance.cluster).exists():
        instance.cluster.delete()
