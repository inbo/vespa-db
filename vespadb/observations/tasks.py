# type: ignore
"""Fetch and update observations from waarnemingen API."""
import logging
from datetime import datetime
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def fetch_observations(self) -> None:
    """Fetch and update observations from waarnemingen API."""
    logger.info("Test task executed at: %s", datetime.now())
    print("Fetching observations... [This is a test task! The current time is: %s]" % datetime.now())