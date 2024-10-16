"""Clean up and audit observation reservations."""

import logging
from datetime import timedelta
from typing import Any

from celery import shared_task
from django.conf import settings
from django.db.models import Count, Q
from django.utils import timezone
from dotenv import load_dotenv

from vespadb.observations.models import Observation
from vespadb.users.models import VespaUser

load_dotenv()

logger = logging.getLogger("vespadb.observations.tasks")


@shared_task
def free_expired_reservations_and_audit_reservation_count(*args: Any, **kwargs: Any) -> None:
    """Free expired reservations and audit the reservation count for each observation."""
    logger.info("start freeing expired reservations")
    cleanup_expired_reservations()
    logger.info("start auditing reservation count")
    audit_user_reservations()
    logger.info("finished freeing expired reservations and auditing reservation count")


def cleanup_expired_reservations() -> None:
    """
    Cleanup reservations that are older than 5 days.

    Check for all observations If the reserved datetime is older than 5 days.
    It will set both reserved_by and reserved_datetime to null.
    If an observation has reserved_datetime but no reserved_by, or vice versa, it will also set reserved_datetime/reserved_by to null.

    This task is intended to be run as a cron job to regularly clean up outdated reservation data.
    """
    five_days_ago = (timezone.now() - timedelta(days=settings.RESERVATION_DURATION_DAYS)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    observations_to_update = Observation.objects.filter(
        Q(reserved_datetime__lte=five_days_ago, reserved_by__isnull=False)
        | Q(reserved_datetime__isnull=False, reserved_by__isnull=True)
        | Q(reserved_datetime__isnull=True, reserved_by__isnull=False)
    )

    for observation in observations_to_update:
        if observation.reserved_datetime and observation.reserved_by:
            # reservation is expired if reserved_datetime is older than 5 days
            if observation.reserved_datetime <= five_days_ago:
                observation.reserved_by = None
                observation.reserved_datetime = None
        elif observation.reserved_datetime and not observation.reserved_by:
            # safety check: if reserved_datetime is set but reserved_by is not, set both to None
            observation.reserved_datetime = None
        elif not observation.reserved_datetime and observation.reserved_by:
            # safety check: if reserved_by is set but reserved_datetime is not, set both to None
            observation.reserved_by = None

        observation.save()

    logger.info("Cleaned up reservation data for %s observations", len(observations_to_update))


def audit_user_reservations() -> None:
    """
    Audit task to verify if the reservation counts of users match the actual reservations in the database.

    This task counts the number of observations reserved by each user, excluding those where eradication has occurred,
    and updates the reservation count if discrepancies are found.
    """
    logger.info("Starting audit of user reservations")

    # Get all users with their actual reservation count from Observation table,
    # excluding observations where eradication_date is set
    actual_counts = (
        Observation.objects.filter(
            eradication_date__isnull=True  # Only include active reservations
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
