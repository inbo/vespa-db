"""Fetch and update observations from waarnemingen API."""

import logging
import os
from datetime import timedelta, datetime
from typing import Any, Optional

import requests
from celery import Task, shared_task
from django.db import models, transaction
from django.utils import timezone
from django.utils.timezone import now
from dotenv import load_dotenv

from vespadb.observations.models import Municipality, Observation, Province
from vespadb.observations.tasks.observation_mapper import map_external_data_to_observation_model
from vespadb.permissions import SYSTEM_USER_OBSERVATION_FIELDS_TO_UPDATE as FIELDS_TO_UPDATE
from vespadb.users.models import UserType
from vespadb.users.utils import get_system_user

load_dotenv()

logger = logging.getLogger("vespadb.observations.tasks")

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
        params: dict[str, str | int | list[str]] = {
            "modified_after": modified_since,
            "limit": 100,
            "offset": offset,
            "validation_status": ["P", "J"],
        }
        response = requests.get(
            "https://waarnemingen.be/api/v1/inbo/vespa-watch/observations/",
            headers=headers,
            params=params,
            timeout=10,
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
        Observation.objects.bulk_create(observations_to_create, batch_size=BATCH_SIZE, ignore_conflicts=True)


def update_observations(observations_to_update: list[Observation], wn_ids_to_update: list[str]) -> None:
    """Update existing observations."""
    observations_update_dict = {obs.wn_id: obs for obs in observations_to_update}
    existing_observations_to_update = Observation.objects.filter(wn_id__in=wn_ids_to_update)
    observations_to_bulk_update = []

    for observation in existing_observations_to_update:
        updated_observation = observations_update_dict[observation.wn_id]
        update_needed = False

        for field in FIELDS_TO_UPDATE:
            if hasattr(observation, field):
                new_value = getattr(updated_observation, field)
                field_type = getattr(Observation, field).field

                if isinstance(field_type, models.ForeignKey):
                    if isinstance(field_type.related_model, Municipality):
                        new_value = updated_observation.municipality_id
                    elif isinstance(field_type.related_model, Province):
                        new_value = updated_observation.province_id

                current_value = getattr(observation, field)
                if current_value != new_value:
                    setattr(observation, field, new_value)
                    update_needed = True

        if update_needed:
            observations_to_bulk_update.append(observation)

    if observations_to_bulk_update:
        logger.info("Updating %s observations", len(observations_to_bulk_update))
        Observation.objects.bulk_update(observations_to_bulk_update, FIELDS_TO_UPDATE, batch_size=BATCH_SIZE)
    else:
        logger.info("No updates required for the observations.")


def fetch_nest_observations(token: str, cluster_id: int) -> list[int]:
    """Fetch all observation IDs associated with a specific nest cluster."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(
            f"https://waarnemingen.be/api/v1/inbo/vespa-watch/nests/{cluster_id}", headers=headers, timeout=10
        )
        response.raise_for_status()
        nest_data = response.json()
        return list(nest_data.get("observation_ids", []))
    except Exception as e:
        logger.exception(f"Error fetching nest observations: {e}")
        return []


def update_observation_visibility(observations: list[Observation], observation_ids_to_hide: set[int]) -> None:
    """Update visibility of observations based on their registration dates."""
    for observation in observations:
        if observation.id in observation_ids_to_hide:
            observation.visible = False
        else:
            observation.visible = True
    Observation.objects.bulk_update(observations, ["visible"], batch_size=BATCH_SIZE)


def fetch_clusters(token: str, limit: int = 100) -> list[dict[str, Any]]:
    """Fetch all clusters from the waarnemingen API with pagination support."""
    url = "https://waarnemingen.be/api/v1/inbo/vespa-watch/nests/"
    headers = {"Authorization": f"Bearer {token}"}
    clusters = []
    offset = 0

    while url:
        params = {"limit": limit, "offset": offset}
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            clusters.extend(data.get("results", []))
            url = data.get("next")  # Handling pagination
            offset += limit
        except requests.RequestException as e:
            logger.exception("Failed to fetch clusters: %s", e)
            break

    return clusters


def manage_observations_visibility(token: str) -> None:
    """Manage visibility of observations for a specific cluster based on their registration dates."""
    clusters = fetch_clusters(token)
    for cluster in clusters:
        observation_ids = cluster.get("observation_ids", [])
        if not observation_ids:
            continue

        observations = list(Observation.objects.filter(wn_id__in=observation_ids))
        if not observations:
            logger.info(f"No observations found for cluster {cluster['id']}.")
            continue  # Skip if no observations are found

        if len(observations) != len(observation_ids):
            logger.info(f"Failed to fetch all observations for cluster {cluster['id']}.")

        observation_dates = {obs.id: obs.observation_datetime for obs in observations}

        # Determine observations to hide
        latest_date = max(observation_dates.values(), default=None)
        if latest_date:
            observation_ids_to_hide = {
                observation_id for observation_id, date in observation_dates.items() if date < latest_date
            }
            update_observation_visibility(observations, observation_ids_to_hide)
            logger.info(f"Updated visibility for {len(observations)} observations in cluster {cluster['id']}.")

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def fetch_and_update_observations(self: Task, since_week: Optional[int] = None, date: Optional[str] = None) -> None:
    """Fetch observations from the waarnemingen API and update the database.

    Observations are fetched in batches and processed in bulk to minimize query overhead.
    Observations can be fetched based on weeks back or a specific date.
    Only observations with a modified by field set to the system user are updated.
    """
    logger.info("Start updating observations")
    token = get_oauth_token()
    if not token:
        raise self.retry(exc=Exception("Failed to obtain OAuth2 token"))

    if date:
        try:
            modified_since = datetime.strptime(date, "%d%m%Y").replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        except ValueError:
            raise ValueError("Invalid date format. Use ddMMyyyy.")
    elif since_week is not None:
        modified_since = (
            (timezone.now() - timedelta(weeks=since_week)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        )
    else:
        raise ValueError("Either since_week or date must be provided.")

    # Pre-fetch existing observations to minimize query overhead
    existing_observations_dict = {obs["wn_id"]: None for obs in Observation.objects.all().values("wn_id")}
    system_user = get_system_user(UserType.SYNC)
    wn_ids_to_update = []
    observations_to_update: list[Observation] = []
    observations_to_create: list[Observation] = []
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
                    wn_ids_to_update.append(wn_id)
                    observations_to_update.append(
                        Observation(wn_id=wn_id, **mapped_data, modified_by=system_user, modified_datetime=current_time)
                    )
                    logger.info("Observation with wn_id %s is ready to be updated.", wn_id)
                elif wn_id not in {obs.wn_id for obs in observations_to_create}:
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
    logger.info("Start managing observations visibility")
    manage_observations_visibility(token)
    logger.info("Finished managing observations visibility")