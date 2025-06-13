from celery import shared_task
from django.core.cache import cache
from vespadb.observations.models import Observation
from django.contrib.gis.db.models.functions import Transform
import json
import logging
from vespadb.observations.utils import get_geojson_cache_key
from vespadb.observations.helpers import parse_and_convert_to_cet
from django.db.models import Q

logger = logging.getLogger(__name__)

@shared_task(name='vespadb.observations.tasks.generate_geojson_task')
def generate_geojson_task(raw_params):
    cache_key = get_geojson_cache_key(raw_params)
    logger.info(f"Using cache key: {cache_key}")

    params = raw_params.copy()
    queryset = Observation.objects.all()

    if 'min_observation_datetime' in params:
        dt_str = params.pop('min_observation_datetime')
        if dt_str:
            queryset = queryset.filter(observation_datetime__gte=parse_and_convert_to_cet(dt_str))
            
    if 'max_observation_datetime' in params:
        dt_str = params.pop('max_observation_datetime')
        if dt_str:
            queryset = queryset.filter(observation_datetime__lte=parse_and_convert_to_cet(dt_str))

    if 'visible' in params:
        value = str(params.pop('visible')).lower()
        if value == 'true':
            queryset = queryset.filter(visible=True)
        elif value == 'false':
            queryset = queryset.filter(visible=False)

    if 'nestType' in params:
        nest_types = params.pop('nestType')
        if nest_types:
            queryset = queryset.filter(nest_type__in=nest_types)

    if 'anbAreasActief' in params:
        value = params.pop('anbAreasActief')
        if value is not None:
             queryset = queryset.filter(anb=value)

    if 'nestStatus' in params:
        statuses = params.pop('nestStatus')
        if statuses:
            status_q_objects = Q()
            if 'open' in statuses:
                status_q_objects |= Q(reserved_by__isnull=True, eradication_result__isnull=True)
            if 'reserved' in statuses:
                status_q_objects |= Q(reserved_by__isnull=False)
            if 'eradicated' in statuses:
                status_q_objects |= Q(eradication_result='successful')
            if 'visited' in statuses:
                status_q_objects |= (Q(eradication_result__isnull=False) & ~Q(eradication_result='successful'))
            
            if status_q_objects:
                queryset = queryset.filter(status_q_objects)

    if 'provinces' in params:
        province_ids = params.pop('provinces')
        if province_ids:
            queryset = queryset.filter(province_id__in=province_ids)

    if 'municipalities' in params:
        municipality_ids = params.pop('municipalities')
        if municipality_ids:
            queryset = queryset.filter(municipality_id__in=municipality_ids)

    if params:
         logger.warning(f"Celery Task: Unhandled filter params: {params}")

    queryset = queryset.annotate(point=Transform("location", 4326))
    
    features = []
    for obs in queryset.iterator(chunk_size=1000):
        current_status = "open"
        if obs.eradication_result == 'successful':
            current_status = "eradicated"
        elif obs.eradication_result is not None:
            current_status = "visited"
        elif obs.reserved_by is not None:
            current_status = "reserved"

        features.append({
            "type": "Feature",
            "properties": {
                "id": obs.id,
                "status": current_status
            },
            "geometry": json.loads(obs.point.geojson) if obs.point else None,
        })

    result = {"type": "FeatureCollection", "features": features}
    cache.set(cache_key, result, 900)
    logger.info(f"Celery Task: GeoJSON generated and cached for key: {cache_key}")
    return result
