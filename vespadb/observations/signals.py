"""Signal handlers for the observations app."""

from typing import Any
import logging
from django.db.models import F, Model
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from vespadb.observations.models import Observation
logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Observation)
def handle_reservation_change(sender, instance, **kwargs):
    """
    Handle changes to the reservation status of an Observation.
    """
    if instance.pk is None:
        # This is a new instance being created; no old instance exists
        logger.debug(f"New observation being created: {instance}")
        return
    
    try:
        old_instance: Observation = sender.objects.get(pk=instance.pk)
        # Compare old_instance.reserved_by with instance.reserved_by or other fields
        if old_instance.reserved_by != instance.reserved_by:
            logger.info(f"Reservation changed for observation {instance.pk}: "
                       f"from {old_instance.reserved_by} to {instance.reserved_by}")
            # Add your logic here (e.g., update reservation count)
    except Observation.DoesNotExist:
        # This shouldn't happen with pk check above, but log it just in case
        logger.error(f"Observation with pk {instance.pk} not found in pre_save signal")

@receiver(post_save, sender=Observation)
def update_reserved_datetime(sender: type[Model], instance: Observation, created: bool, **kwargs: Any) -> None:
    """
    Update reserved_datetime and handle reservation count on eradication update for an Observation after it has been saved.

    This signal sets the reserved_datetime to the current time when a reservation is made, if it was not already set.
    Also, if eradication_date was not previously filled but is updated now, and if reserved_by was set,
    it decrements the reservation count for the user that reserved the observation.

    Parameters
    ----------
        sender (Type[Model]): The model class that sent the signal.
        instance (Observation): The newly saved observation instance.
        created (bool): Flag indicating whether this was a creation or an update.
        **kwargs: Extra keyword arguments.
    """
    if instance.reserved_by and not instance.reserved_datetime:
        instance.reserved_datetime = timezone.now()
        instance.save(update_fields=["reserved_datetime"])

    if not created:
        old_instance = sender.objects.get(pk=instance.pk)
        # Check if eradication_date was updated and reserved by is set
        if not old_instance.eradication_date and instance.eradication_date and instance.reserved_by:
            instance.reserved_by.reservation_count = F("reservation_count") - 1
            instance.reserved_by.save(update_fields=["reservation_count"])
