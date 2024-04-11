"""Fetch and update observations from waarnemingen API."""

import logging
import os
from datetime import timedelta
from typing import Any

import requests
from celery import Task, shared_task
from django.utils import timezone
from dotenv import load_dotenv

from vespadb.observations.models import Observation
from vespadb.observations.observation_mapper import map_external_data_to_observation_model

load_dotenv()

logger = logging.getLogger(__name__)


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
    headers = {"Authorization": f"Bearer {token}"}
    params: dict[str, str | int] = {
        "modified_since": modified_since,
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


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def fetch_and_update_observations(self: Task) -> None:
    """Fetch and update observations from waarnemingen.be."""
    token = get_oauth_token()
    if not token:
        # If token is None, schedule a retry
        raise self.retry(exc=Exception("Failed to obtain OAuth2 token"))

    modified_since = (timezone.now() - timedelta(weeks=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    offset = 0
    created = 0
    updated = 0

    while True:
        try:
            response = requests.get(
                str(os.environ.get("WAARNEMINGEN_OBSERVATIONS_URL")),
                headers={"Authorization": f"Bearer {token}"},
                params={"modified_since": modified_since, "offset": offset, "limit": 100},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            for external_data in data["results"]:
                mapped_data = map_external_data_to_observation_model(external_data)
                if mapped_data is None:
                    continue  # Skip this observation due to errors in the data

                _, created = Observation.objects.update_or_create(
                    wn_id=mapped_data["wn_id"],
                    defaults=mapped_data,
                )
                if created:
                    logger.info(
                        "Created new observation with wn_id %s and internal id %s",
                        mapped_data["wn_id"],
                        mapped_data["id"],
                    )
                    created += 1
                else:
                    logger.info(
                        "Updated observation with wn_id %s and internal id %s", mapped_data["wn_id"], mapped_data["id"]
                    )
                    updated += 1

            if not data.get("next"):  # If there's no next page, break from the loop
                break
            offset += len(data["results"])
        except requests.RequestException:
            logger.exception("Failed to fetch observations")
            break  # Stop the process in case of a request failure

    logger.info("Finished processing %s observations. Created %s, Updated %s", created + updated, created, updated)
