from celery import shared_task
from django.core.cache import cache
from vespadb.observations.models import Observation
from django.contrib.gis.db.models.functions import Transform
import json
import logging

logger = logging.getLogger(__name__)

@shared_task(name='vespadb.observations.tasks.generate_geojson_task')
def generate_geojson_task(query_params, cache_key):
    # Convert custom datetime filters into valid Django lookups.
    if 'min_observation_datetime' in query_params:
        query_params['observation_datetime__gte'] = query_params.pop('min_observation_datetime')
    if 'max_observation_datetime' in query_params:
        query_params['observation_datetime__lte'] = query_params.pop('max_observation_datetime')

    # Convert the "visible" parameter from string to boolean if necessary.
    if 'visible' in query_params:
        value = query_params['visible']
        if isinstance(value, str):
            query_params['visible'] = value.lower() == 'true'
    
    logger.info(f"Generating GeoJSON for {query_params}")
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
