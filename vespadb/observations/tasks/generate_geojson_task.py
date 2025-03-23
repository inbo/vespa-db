from celery import shared_task
from django.core.cache import cache
from vespadb.observations.models import Observation
from django.contrib.gis.db.models.functions import Transform
import json

@shared_task
def generate_geojson_task(query_params, cache_key):
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
    cache.set(cache_key, result, 900)  # 15-minute expiration
    return result
