"""Import a specific observation from waarnemingen.be by its ID.

Usage:
python manage.py import_observation_by_id <waarnemingen_id>

example:
python manage.py import_observation_by_id 12345
"""

import logging
from typing import Any, Optional

import requests
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.timezone import now

from vespadb.observations.models import Observation
from vespadb.observations.tasks.observation_mapper import map_external_data_to_observation_model
from vespadb.observations.tasks.observation_sync import get_oauth_token
from vespadb.users.models import UserType
from vespadb.users.utils import get_system_user

logger = logging.getLogger("vespadb.observations.commands")
logger.setLevel(logging.DEBUG)

class Command(BaseCommand):
    """Import a specific observation from waarnemingen.be by its ID."""

    help = "Import a specific observation from waarnemingen.be by its ID."

    def add_arguments(self, parser):
        """Add arguments to the command."""
        parser.add_argument("waarnemingen_id", type=int, help="The ID of the observation from waarnemingen.be")

    def handle(self, *args: Any, **options: Any) -> None:
        """
        Import a specific observation from waarnemingen.be by its ID.
        
        Args:
            waarnemingen_id: The ID of the observation from waarnemingen.be
            
        Returns:
            None: Prints the local database ID to the console
        """
        waarnemingen_id = options["waarnemingen_id"]
        self.stdout.write(f"Importing observation with waarnemingen.be ID: {waarnemingen_id}")
        
        # Get authentication token
        token = get_oauth_token()
        if not token:
            raise CommandError("Failed to obtain OAuth2 token from waarnemingen.be")
        
        # Fetch the specific observation
        observation_data = self.fetch_observation(token, waarnemingen_id)
        if not observation_data:
            raise CommandError(f"Failed to fetch observation with ID {waarnemingen_id} from waarnemingen.be")
        
        # Map and save the observation
        system_user = get_system_user(UserType.SYNC)
        current_time = now()
        
        try:
            # Check if observation already exists in the database
            try:
                existing_obs = Observation.objects.get(wn_id=waarnemingen_id)
                self.stdout.write(f"Observation already exists with ID: {existing_obs.id}")
                return existing_obs.id
            except Observation.DoesNotExist:
                # Map the observation data from the API to our model
                mapped_data = map_external_data_to_observation_model(observation_data)
                if not mapped_data:
                    raise CommandError(f"Failed to map observation data for ID {waarnemingen_id}")
                
                # Get the wn_id and remove it from the mapped data
                wn_id = mapped_data.pop("wn_id")
                
                # Create the new observation
                with transaction.atomic():
                    observation = Observation.objects.create(
                        wn_id=wn_id,
                        **mapped_data,
                        created_by=system_user,
                        modified_by=system_user,
                        created_datetime=current_time,
                        modified_datetime=current_time,
                    )
                
                # Print and return the ID
                self.stdout.write(self.style.SUCCESS(f"{observation.id}"))
                return observation.id
                
        except Exception as e:
            logger.exception(f"Error importing observation {waarnemingen_id}: {e}")
            raise CommandError(f"Error importing observation: {str(e)}")

    def fetch_observation(self, token: str, observation_id: int) -> Optional[dict[str, Any]]:
        """
        Fetch a single observation from waarnemingen.be API.
        
        Args:
            token: OAuth2 token for authentication
            observation_id: The ID of the observation to fetch
            
        Returns:
            The observation data as a dictionary or None if the request failed
        """
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                f"https://waarnemingen.be/api/v1/inbo/vespa-watch/observations/{observation_id}/",
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.exception(f"Error fetching observation {observation_id}: {e}")
            return None
