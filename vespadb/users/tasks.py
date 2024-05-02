"""User tasks for the VespaDB application."""

import logging

from celery import shared_task
from django.db.models import Count

from vespadb.observations.models import Observation
from vespadb.users.models import VespaUser

logger = logging.getLogger(__name__)


@shared_task
def audit_user_reservations() -> None:
    """
    Audit task to verify if the reservation counts of users match the actual reservations in the database.

    This task counts the number of observations reserved by each user, excluding those where eradication has occurred,
    and updates the reservation count if discrepancies are found.
    """
    logger.info("Starting audit of user reservations")

    # Get all users with their actual reservation count from Observation table,
    # excluding observations where eradication_datetime is set
    actual_counts = (
        Observation.objects.filter(
            eradication_datetime__isnull=True  # Only include active reservations
        )
        .values("reserved_by")
        .annotate(actual_count=Count("id"))
        .order_by()
    )

    # Update users where the actual reservation count does not match the recorded count
    for count_data in actual_counts:
        user_id = count_data["reserved_by"]
        if user_id is None:
            continue  # Skip entries where reserved_by is None
        actual_count = count_data["actual_count"]
        user = VespaUser.objects.get(id=user_id)  # Retrieve user by ID

        # Check if the current stored reservation count matches the actual count
        if user.reservation_count != actual_count:
            logger.info(
                f"Updating reservation count for user {user.username}: {user.reservation_count} -> {actual_count}"
            )
            user.reservation_count = actual_count
            user.save()

    logger.info("Audit of user reservations completed")
