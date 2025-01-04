from celery import shared_task
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
import logging
from typing import Dict, Any, Optional, Set
from vespadb.users.models import VespaUser as User
from vespadb.observations.models import Export
from .export_utils import CSV_HEADERS, prepare_row_data

logger = logging.getLogger(__name__)

@shared_task(
    name="generate_export",
    max_retries=3,
    default_retry_delay=60,
    soft_time_limit=1700,
    time_limit=1800,
    acks_late=True
)
def generate_export(export_id: int, filters: Dict[str, Any], user_id: Optional[int] = None) -> Dict[str, Any]:
    """Generate CSV export of observations based on filters."""
    logger.info(f"Starting export {export_id} for user {user_id} with filters: {filters}")
    export = Export.objects.get(id=export_id)

    try:
        # Update export status
        export.status = 'processing'
        export.save()

        from ..models import Observation  # Import here to avoid circular imports
        # Apply filters and get initial count
        queryset = Observation.objects.filter(**filters)
        initial_count = queryset.count()
        logger.info(f"Initial queryset count: {initial_count}")

        # Add optimizations
        queryset = (queryset
                   .select_related('province', 'municipality', 'reserved_by')
                   .order_by('id'))
        
        # Process in batches
        batch_size = 1000
        processed = 0
        rows = [CSV_HEADERS]  # Start with headers
        
        # Get user permissions
        is_admin = False
        user_municipality_ids: Set[str] = set()
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                is_admin = user.is_superuser
                user_municipality_ids = set(user.municipalities.values_list('id', flat=True))
            except User.DoesNotExist:
                logger.warning(f"User {user_id} not found")
        
        # Process in batches to reduce memory usage
        for i in range(0, initial_count, batch_size):
            batch = queryset[i:i + batch_size]
            batch_rows = []
            
            for observation in batch:
                try:
                    row = prepare_row_data(observation, is_admin, user_municipality_ids)
                    batch_rows.append(row)
                    processed += 1
                    
                    if processed % 100 == 0:
                        progress = int((processed / initial_count) * 100)
                        export.progress = progress
                        export.save()
                        logger.info(f"Processed {processed}/{initial_count} records")
                except Exception as e:
                    logger.error(f"Error processing observation {observation.id}: {e}")
                    continue
            
            # Add batch to rows and clear batch data
            rows.extend(batch_rows)
            batch_rows = []
        
        # Store in cache
        cache_key = f'export_{export_id}_data'
        cache.set(cache_key, rows, timeout=3600)

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
            'total_processed': processed
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
