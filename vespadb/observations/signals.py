"""Signal handlers for the observations app."""

from typing import Any

from django.db.models import Model
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.db.models import F

from vespadb.observations.models import Observation


@receiver(pre_save, sender=Observation)
def handle_reservation_change(sender: type[Model], instance: Observation, **kwargs: Any) -> None:
    """
    Signal to handle changes in reservation ownership before an Observation is saved.

    If the reserved_by user changes, adjust the reservation count for the previously
    reserved user and the newly reserved user. Decrease the count for the old user
    and increase it for the new user.

    Parameters
    ----------
        sender (Type[Model]): The model class that sent the signal.
        instance (Observation): The observation instance being saved.
        **kwargs: Extra keyword arguments.
    """
    if instance.pk:
        old_instance: Observation = sender.objects.get(pk=instance.pk)
        if old_instance.reserved_by != instance.reserved_by:
            if old_instance.reserved_by:
                old_instance.reserved_by.reservation_count -= 1
                old_instance.reserved_by.save()
            if instance.reserved_by:
                instance.reserved_by.reservation_count += 1
                instance.reserved_by.save()


@receiver(post_save, sender=Observation)
def update_reserved_datetime(sender: type[Model], instance: Observation, created: bool, **kwargs: Any) -> None:
    """
    Update reserved_datetime and handle reservation count on eradication update for an Observation after it has been saved.

    This signal sets the reserved_datetime to the current time when a reservation is made, if it was not already set.
    Also, if eradication_datetime was not previously filled but is updated now, and if reserved_by was set,
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
        # Check if eradication_datetime was updated
        if not old_instance.eradication_datetime and instance.eradication_datetime:
            # Ensure that reserved_by is also set
            if instance.reserved_by:
                instance.reserved_by.reservation_count = F('reservation_count') - 1
                instance.reserved_by.save(update_fields=["reservation_count"])