# vespadb/observations/tasks/cache_rebuild.py

from celery import shared_task
from django.core.cache import cache
import logging

# Import the tasks and configs
from .generate_geojson_task import generate_geojson_task
from vespadb.observations.cache_configs import PREWARM_CONFIGS

logger = logging.getLogger(__name__)

# Define a lock key and timeout (in seconds)
REBUILD_LOCK_KEY = "vespadb::rebuild_geojson_lock"
LOCK_EXPIRE = 60 * 5  # Lock expires in 5 minutes to prevent it from getting stuck

@shared_task(name="vespadb.observations.tasks.rebuild_all_prewarmed_caches")
def rebuild_all_prewarmed_caches():
    """
    Safely triggers regeneration of all pre-warmed GeoJSON caches.
    Uses a cache lock to prevent multiple concurrent runs (thundering herd).
    """
    # The `nx=True` argument makes this an atomic "add if not exists" operation.
    # This is the core of the locking mechanism.
    if cache.add(REBUILD_LOCK_KEY, "locked", timeout=LOCK_EXPIRE):
        logger.info("Acquired lock, starting GeoJSON pre-warmed cache regeneration.")
        try:
            # Loop through all defined configurations and schedule a generation task for each
            for config in PREWARM_CONFIGS:
                generate_geojson_task.delay(config['params'])
            logger.info(f"Successfully scheduled {len(PREWARM_CONFIGS)} GeoJSON regeneration tasks.")
        finally:
            # Always release the lock when done
            cache.delete(REBUILD_LOCK_KEY)
            logger.info("Released GeoJSON regeneration lock.")
    else:
        logger.info("GeoJSON regeneration is already in progress. Skipping duplicate request.")
