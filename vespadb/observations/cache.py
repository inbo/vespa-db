from django.core.cache import cache
import logging
from vespadb.observations.tasks.cache_rebuild import rebuild_all_prewarmed_caches

logger = logging.getLogger(__name__)

def invalidate_geojson_cache() -> None:
    """
    Invalidate all GeoJSON-related caches and trigger a safe, locked regeneration.
    """
    pattern = "vespadb::/observations/dynamic-geojson/*"
    keys = cache.keys(pattern)
    if keys:
        cache.delete_many(keys)
        logger.info(f"Invalidated {len(keys)} GeoJSON caches matching pattern '{pattern}'")

    # Asynchronously schedule the master rebuild task.
    # The lock inside the task will prevent system overload.
    logger.info("Scheduling a task to regenerate all pre-warmed GeoJSON caches.")
    rebuild_all_prewarmed_caches.delay()


def invalidate_observation_cache(observation_id: str) -> None:
    """Invalidate the cache for a single observation."""
    cache_key = f"vespadb::observations::{observation_id}"
    cache.delete(cache_key)
