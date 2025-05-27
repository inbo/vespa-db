from celery import shared_task
from django.core.cache import cache
from vespadb.observations.models import Observation
from django.contrib.gis.db.models.functions import Transform
import json
import logging
from vespadb.observations.utils import get_geojson_cache_key
from vespadb.observations.helpers import parse_and_convert_to_cet

logger = logging.getLogger(__name__)

@shared_task(name='vespadb.observations.tasks.generate_geojson_task')
def generate_geojson_task(raw_params):
    # Compute the cache key from the raw parameters.
    cache_key = get_geojson_cache_key(raw_params)
    logger.info(f"Using cache key: {cache_key}")
    # Make a copy for transforming parameters for filtering.
    query_params = raw_params.copy()
    if 'min_observation_datetime' in query_params:
        dt_str = query_params.pop('min_observation_datetime')
        query_params['observation_datetime__gte'] = parse_and_convert_to_cet(dt_str)
    if 'max_observation_datetime' in query_params:
        dt_str = query_params.pop('max_observation_datetime')
        query_params['observation_datetime__lte'] = parse_and_convert_to_cet(dt_str)

    if 'visible' in query_params:
        value = query_params['visible']
        if isinstance(value, str):
            query_params['visible'] = value.lower() == 'true'
    queryset = Observation.objects.filter(**query_params).annotate(point=Transform("location", 4326))
    features = [
        {
            "type": "Feature",
            "properties": {
                "id": obs.id,
                "status": "eradicated" if obs.eradication_result else "reserved" if obs.reserved_by else "default"
            },
            "geometry": json.loads(obs.point.geojson) if obs.point else None,
        }
        for obs in queryset.iterator(chunk_size=1000)
    ]
    result = {"type": "FeatureCollection", "features": features}
    cache.set(cache_key, result, 900)  # Cache for 15 minutes
    return result
