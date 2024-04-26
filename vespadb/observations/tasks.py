"""Fetch and update observations from waarnemingen API."""

import logging
import os
from datetime import timedelta
from typing import Any

import requests
from celery import Task, shared_task
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.timezone import now
from dotenv import load_dotenv

from vespadb.observations.models import Municipality, Observation, Province
from vespadb.observations.observation_mapper import map_external_data_to_observation_model
from vespadb.permissions import SYSTEM_USER_OBSERVATION_FIELDS_TO_UPDATE as FIELDS_TO_UPDATE
from vespadb.users.models import UserType
from vespadb.users.utils import get_system_user

load_dotenv()

logger = logging.getLogger(__name__)

BATCH_SIZE = 500


def get_oauth_token() -> str | None:
    """Authenticate with the waarnemingen API to obtain an OAuth2 token."""
    data = {
        "grant_type": "password",
        "email": os.environ.get("WN_EMAIL"),
        "password": os.environ.get("WN_PASSWORD"),
        "client_id": os.environ.get("WN_CLIENT_ID"),
        "client_secret": os.environ.get("WN_CLIENT_SECRET"),
        "type": "confidential",
    }
    try:
        response = requests.post(str(os.environ.get("WAARNEMINGEN_TOKEN_URL")), data=data, timeout=10)
        response.raise_for_status()
        token_data = response.json()
        if token_data.get("access_token"):
            return str(token_data["access_token"])
    except requests.HTTPError:
        logger.exception("HTTP error occurred")
        logger.exception("Response status: %s, Response body: %s", response.status_code, response.text)
    except requests.RequestException:
        logger.exception("Error obtaining OAuth2 token")
    return None


def fetch_observations_page(token: str, modified_since: str, offset: int = 0) -> dict[str, Any]:
    """Fetch a page of observations."""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        params: dict[str, str | int] = {
            "modified_after": modified_since,
            "limit": 100,
            "offset": offset,
        }
        response = requests.get(
            str(os.environ.get("WAARNEMINGEN_OBSERVATIONS_URL")), headers=headers, params=params, timeout=10
        )
        response.raise_for_status()
        json_response = response.json()
        if isinstance(json_response, dict):
            return json_response
        raise ValueError("Unexpected response format from API")
    except requests.RequestException:
        logger.exception("Error fetching observations page")
        return {}


def cache_wn_ids() -> set[str]:
    """Cache wn_ids from the database to minimize query overhead."""
    return set(Observation.objects.values_list("wn_id", flat=True))


def create_observations(observations_to_create: list[Observation]) -> None:
    """Bulk create observations."""
    if observations_to_create:
        Observation.objects.bulk_create(observations_to_create, batch_size=BATCH_SIZE)


def update_observations(observations_to_update: list[Observation], wn_ids_to_update: list[str]) -> None:
    """Update existing observations."""
    # Map updated observations by wn_id for easy access during update
    observations_update_dict = {obs.wn_id: obs for obs in observations_to_update}
    # Fetch all observations to be updated from the database in one query
    existing_observations_to_update = Observation.objects.filter(wn_id__in=wn_ids_to_update)
    for observation in existing_observations_to_update:
        updated_observation = observations_update_dict[observation.wn_id]
        for field in FIELDS_TO_UPDATE:
            if hasattr(observation, field):
                new_value = getattr(updated_observation, field)
                field_type = getattr(Observation, field).field

                if isinstance(field_type, models.ForeignKey):
                    # Check if the field is a foreign key relation to Municipality or Province
                    if isinstance(field_type.related_model, Municipality):
                        new_value = updated_observation.municipality_id
                    elif isinstance(field_type.related_model, Province):
                        new_value = updated_observation.province_id
                setattr(observation, field, new_value)

    logger.info("Updating %s observations", len(existing_observations_to_update))
    Observation.objects.bulk_update(existing_observations_to_update, FIELDS_TO_UPDATE, batch_size=BATCH_SIZE)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def fetch_and_update_observations(self: Task) -> None:
    """Fetch observations from the waarnemingen API and update the database.

    Observations are fetched in batches and processed in bulk to minimize query overhead.
    All observations that have been modified by waarnmeingen in the last two weeks are fetched.
    Only observations with a modified by field set to the system user are updated.
    """
    logger.info("start updating observations")
    token = get_oauth_token()
    if not token:
        raise self.retry(exc=Exception("Failed to obtain OAuth2 token"))

    modified_since = (
        (timezone.now() - timedelta(weeks=2)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    )

    # Pre-fetch existing observations to minimize query overhead
    existing_observations_dict = {
        obs["wn_id"]: obs["modified_by"] for obs in Observation.objects.all().values("wn_id", "modified_by")
    }
    system_user = get_system_user(UserType.SYNC)
    observations_to_create, wn_ids_to_update = [], []
    observations_to_update: list[Observation] = []
    offset = 0
    while True:
        data = fetch_observations_page(token, modified_since, offset)

        if data:
            for external_data in data["results"]:
                mapped_data = map_external_data_to_observation_model(external_data)
                current_time = now()

                if mapped_data is None:
                    continue

                wn_id = mapped_data.pop("wn_id")

                if wn_id in existing_observations_dict:
                    # Check if modified_by is system_user before update
                    if existing_observations_dict[wn_id] == system_user.id:
                        # Update only observations that have been modified by the system user
                        # This is to prevent overwriting manual changes made by users
                        wn_ids_to_update.append(wn_id)
                        observations_to_update.append(
                            Observation(
                                wn_id=wn_id, **mapped_data, modified_by=system_user, modified_datetime=current_time
                            )
                        )
                        logger.info("Observation with wn_id %s is ready to be updated.", wn_id)
                else:
                    observations_to_create.append(
                        Observation(
                            wn_id=wn_id,
                            **mapped_data,
                            created_by=system_user,
                            modified_by=system_user,
                            created_datetime=current_time,
                            modified_datetime=current_time,
                        )
                    )
                    logger.info("Observation with wn_id %s is ready to be created.", wn_id)

            if not data.get("next"):
                break
        else:
            logger.error("No data retrieved, breaking out of the loop.")
            break
        offset += len(data["results"])

    logger.info("Fetched %s observations", len(observations_to_create) + len(observations_to_update))
    logger.info(
        "Creating %s observations, updating %s observations", len(observations_to_create), len(observations_to_update)
    )
    with transaction.atomic():  # Ensure that all operations are atomic
        create_observations(observations_to_create)
        update_observations(observations_to_update, wn_ids_to_update)

    logger.info(
        "Finished processing observations. Created: %s, Updated: %s",
        len(observations_to_create),
        len(observations_to_update),
    )


@shared_task
def cleanup_expired_reservations() -> None:
    """
    Cleanup reservations that are older than 2 weeks.

    Check for all observations If the reserved datetime is older than 2 weeks.
    It will set both reserved_by and reserved_datetime to null.
    If an observation has reserved_datetime but no reserved_by, or vice versa, it will also set reserved_datetime/reserved_by to null.

    This task is intended to be run as a cron job to regularly clean up outdated reservation data.
    """
    two_weeks_ago = (timezone.now() - timedelta(weeks=2)).replace(hour=0, minute=0, second=0, microsecond=0)
    observations_to_update = Observation.objects.filter(
        Q(reserved_datetime__lte=two_weeks_ago, reserved_by__isnull=False)
        | Q(reserved_datetime__isnull=False, reserved_by__isnull=True)
        | Q(reserved_datetime__isnull=True, reserved_by__isnull=False)
    )

    for observation in observations_to_update:
        if observation.reserved_datetime and observation.reserved_by:
            # reservation is expired if reserved_datetime is older than two weeks
            if observation.reserved_datetime <= two_weeks_ago:
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


fetch_and_update_observations()
