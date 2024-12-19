import csv
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Set, Iterator
from django.core.cache import cache
from django.db import models, transaction
from django.utils import timezone
from celery import shared_task
from vespadb.observations.models import Observation, Export
from vespadb.users.models import VespaUser as User
from vespadb.observations.serializers import user_read_fields, public_read_fields

logger = logging.getLogger(__name__)

CSV_HEADERS = [
    "id", "created_datetime", "modified_datetime", "latitude", "longitude", 
    "source", "source_id", "nest_height", "nest_size", "nest_location", 
    "nest_type", "observation_datetime", "province", "eradication_date", 
    "municipality", "images", "anb_domain", "notes", "eradication_result", 
    "wn_id", "wn_validation_status", "nest_status"
]

class Echo:
    """An object that implements just the write method of the file-like interface."""
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value

def get_status(observation: Observation) -> str:
    """Get observation status string."""
    if observation.eradication_result:
        return "eradicated"
    if observation.reserved_by:
        return "reserved"
    return "untreated"

def _prepare_row_data(
    observation: Observation,
    is_admin: bool,
    user_municipality_ids: Set[str]
) -> List[str]:
    """
    Prepare a single row of data for the CSV export with error handling.
    """
    try:
        # Determine allowed fields based on permissions
        if is_admin or (observation.municipality_id in user_municipality_ids):
            allowed_fields = user_read_fields
        else:
            allowed_fields = public_read_fields
            
        allowed_fields.extend(["source_id", "latitude", "longitude", "anb_domain", "nest_status"])
        
        row_data = []
        for field in CSV_HEADERS:
            try:
                if field not in allowed_fields:
                    row_data.append("")
                    continue

                if field == "latitude":
                    row_data.append(str(observation.location.y) if observation.location else "")
                elif field == "longitude":
                    row_data.append(str(observation.location.x) if observation.location else "")
                elif field in ["created_datetime", "modified_datetime", "observation_datetime"]:
                    datetime_val = getattr(observation, field, None)
                    if datetime_val:
                        datetime_val = datetime_val.replace(microsecond=0)
                        row_data.append(datetime_val.isoformat() + "Z")
                    else:
                        row_data.append("")
                elif field == "province":
                    row_data.append(observation.province.name if observation.province else "")
                elif field == "municipality":
                    row_data.append(observation.municipality.name if observation.municipality else "")
                elif field == "anb_domain":
                    row_data.append(str(observation.anb))
                elif field == "nest_status":
                    row_data.append(get_status(observation))
                elif field == "source_id":
                    row_data.append(str(observation.source_id) if observation.source_id is not None else "")
                else:
                    value = getattr(observation, field, "")
                    row_data.append(str(value) if value is not None else "")
            except Exception as e:
                logger.warning(f"Error processing field {field} for observation {observation.id}: {str(e)}")
                row_data.append("")
                
        return row_data
    except Exception as e:
        logger.error(f"Error preparing row data for observation {observation.id}: {str(e)}")
        return [""] * len(CSV_HEADERS)

def parse_boolean(value: str) -> bool:
    """
    Convert a string value to a boolean.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        value_lower = value.lower()
        if value_lower in {"true", "1"}:
            return True
        elif value_lower in {"false", "0"}:
            return False
    raise ValueError(f"Invalid boolean value: {value}")

def generate_rows(queryset, is_admin: bool, user_municipality_ids: set) -> Iterator[List[str]]:
    """Generate rows for CSV streaming."""
    # First yield the headers
    yield CSV_HEADERS
    
    # Then yield the data rows
    for observation in queryset:
        try:
            row = _prepare_row_data(observation, is_admin, user_municipality_ids)
            yield row
        except Exception as e:
            logger.error(f"Error processing observation {observation.id}: {str(e)}")
            continue

@shared_task(
    name="generate_export",
    max_retries=3,
    default_retry_delay=60,
    soft_time_limit=1700,
    time_limit=1800,
    acks_late=True
)
def generate_export(export_id: int, filters: Dict[str, Any], user_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Generate CSV export of observations based on filters.
    
    Args:
        export_id: ID of the Export record
        filters: Dictionary of filters to apply to the queryset
        user_id: Optional ID of the user requesting the export
    
    Returns:
        Dictionary containing export status and details
    """
    logger.info(f"Starting export {export_id} for user {user_id}")
    export = Export.objects.get(id=export_id)

    try:
        # Update export status
        export.status = 'processing'
        export.save()
        logger.info(f"Export {export_id} status set to processing")

        # Validate and preprocess filters
        valid_fields = {field.name: field for field in Observation._meta.get_fields()}
        processed_filters = {}
        for key, value in filters.items():
            if key in valid_fields:
                field = valid_fields[key]
                if isinstance(field, models.BooleanField):
                    try:
                        processed_filters[key] = parse_boolean(value)
                    except ValueError:
                        logger.error(f"Invalid boolean value for filter {key}: {value}")
                        continue
                else:
                    processed_filters[key] = value

        # Prepare queryset with optimizations
        queryset = (Observation.objects
                   .filter(**processed_filters)
                   .select_related('province', 'municipality', 'reserved_by')
                   .order_by('id'))
        
        total = queryset.count()
        processed = 0
        
        is_admin = False
        user_municipality_ids = set()
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                is_admin = user.is_superuser
                user_municipality_ids = set(user.municipalities.values_list('id', flat=True))
            except User.DoesNotExist:
                pass
                
        logger.info(f"Processing {total} observations for export {export_id}")

        # Generate CSV data
        rows = list(generate_rows(queryset, is_admin, user_municipality_ids))
        
        # Store in cache
        cache_key = f'export_{export_id}_data'
        cache.set(cache_key, rows, timeout=3600)  # Store for 1 hour

        # Update export record
        with transaction.atomic():
            export.status = 'completed'
            export.completed_at = timezone.now()
            export.progress = 100
            export.save()

        logger.info(f"Export {export_id} completed successfully")

        return {
            'status': 'completed',
            'cache_key': cache_key,
            'total_processed': total
        }

    except Exception as e:
        logger.exception(f"Export {export_id} failed: {str(e)}")
        export.status = 'failed'
        export.error_message = str(e)
        export.save()
        raise

@shared_task
def cleanup_old_exports() -> None:
    """Clean up exports older than 24 hours."""
    logger.info("Starting cleanup of old exports")
    cutoff = timezone.now() - timedelta(days=1)
    old_exports = Export.objects.filter(created_at__lt=cutoff)
    
    for export in old_exports:
        # Remove from cache if exists
        cache_key = f'export_{export.id}_data'
        cache.delete(cache_key)
        
        # Delete the export record
        export.delete()
        logger.info(f"Cleaned up export {export.id}")
