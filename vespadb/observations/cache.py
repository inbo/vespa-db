"""."""

from django.core.cache import cache
from vespadb.observations.tasks.generate_geojson_task import generate_geojson_task
import logging

logger = logging.getLogger(__name__)

def invalidate_geojson_cache() -> None:
    """Invalidate the cache for all GeoJSON observations."""
    keys = cache.keys("vespadb::/observations/dynamic-geojson/*")
    cache.delete_many(keys)
    # Trigger the celery task to rebuild the cache with your default parameters.
    default_params = {'visible': 'true', 'min_observation_datetime': '2024-04-01T00:00:00+02:00'}
    # This schedules the task asynchronously.
    logger.info("Scheduling task to regenerate GeoJSON cache")
    generate_geojson_task(default_params)

def invalidate_observation_cache(observation_id: str) -> None:
    """Invalidate the cache for a single observation."""
    cache_key = f"vespadb::observations::{observation_id}"
    cache.delete(cache_key)
