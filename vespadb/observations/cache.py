"""."""

from django.core.cache import cache


def invalidate_geojson_cache() -> None:
    """Invalidate the cache for all GeoJSON observations."""
    keys = cache.keys("vespadb::/observations/dynamic-geojson*")
    cache.delete_many(keys)


def invalidate_observation_cache(observation_id: str) -> None:
    """Invalidate the cache for a single observation."""
    cache_key = f"vespadb::observations::{observation_id}"
    cache.delete(cache_key)
