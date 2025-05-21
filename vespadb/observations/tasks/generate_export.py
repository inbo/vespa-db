from typing import Iterator, List, Set, Any, Union, Protocol, Optional, Dict
from django.core.files.storage import default_storage
from django.db.models.query import QuerySet
from django.db.models import Model
from django.utils import timezone
from datetime import timedelta
import csv
import io
import logging
from celery import shared_task
from vespadb.observations.models import Observation, Export
from vespadb.users.models import VespaUser as User
import pytz

logger = logging.getLogger(__name__)

class WriterProtocol(Protocol):
    def writerow(self, row: List[str]) -> Any: ...

PUBLIC_FIELDS = [
    "id",
    "observation_datetime",
    "latitude",
    "longitude",
    "province",
    "municipality",
    "anb_domain",
    "nest_status",
    "eradication_date",
    "eradication_result",
    "images",
    "nest_type",
    "nest_location",
    "nest_height",
    "nest_size",
    "notes",
    "source",
    "source_id",
    "wn_id",
    "wn_validation_status",
    "wn_cluster_id",
    "created_datetime",
    "modified_datetime",
]

def get_status(observation: Observation) -> str:
    """Get observation status string."""
    if observation.eradication_result:
        return "eradicated"
    if observation.reserved_by:
        return "reserved"
    return "untreated"

def prepare_row_data(
    observation: Observation,
    is_admin: bool,
    user_municipality_ids: Set[str]
) -> List[str]:
    """Prepare a single row of data for CSV export."""
    try:
        row_data: List[str] = []
        for field in PUBLIC_FIELDS:
            try:
                if field == "latitude":
                    row_data.append(str(observation.location.y) if observation.location else "")
                elif field == "longitude":
                    row_data.append(str(observation.location.x) if observation.location else "")
                elif field in ["created_datetime", "modified_datetime", "observation_datetime"]:
                    datetime_val = getattr(observation, field, None)
                    if datetime_val:
                        from vespadb.observations.helpers import parse_and_convert_to_cet
                        datetime_val = parse_and_convert_to_cet(datetime_val)
                        datetime_val = datetime_val.replace(microsecond=0)
                        # Format as CET without timezone indicator
                        row_data.append(datetime_val.strftime("%Y-%m-%dT%H:%M:%S"))
                    else:
                        row_data.append("")
                elif field == "province":
                    row_data.append(observation.province.name if observation.province else "")
                elif field == "municipality":
                    row_data.append(observation.municipality.name if observation.municipality else "")
                elif field == "nest_status":
                    row_data.append(get_status(observation))
                elif field == "eradication_date":
                    date_val = getattr(observation, "eradication_date", None)
                    row_data.append(date_val.strftime("%Y-%m-%d") if date_val else "")
                elif field == "eradication_result":
                    value = getattr(observation, "eradication_result", "")
                    row_data.append(str(value) if value is not None else "")
                elif field == "images":
                    value = getattr(observation, "images", [])
                    if isinstance(value, list):
                        if not value:
                            row_data.append("")
                        elif len(value) == 1:
                            row_data.append(value[0])
                        else:
                            joined = ",".join(value)
                            row_data.append(joined)
                    else:
                        s = str(value)
                        if s.startswith("[") and s.endswith("]"):
                            s = s[1:-1].strip()
                            parts = [part.strip().strip("'").strip('"') for part in s.split(",") if part.strip()]
                            if not parts:
                                row_data.append("")
                            elif len(parts) == 1:
                                row_data.append(parts[0])
                            else:
                                joined = ",".join(parts)
                                row_data.append(joined)
                        else:
                            row_data.append(s)
                elif field == "notes":
                    value = getattr(observation, "notes", "")
                    row_data.append(str(value) if value is not None else "")
                elif field == "wn_id":
                    value = getattr(observation, "wn_id", "")
                    row_data.append(str(value) if value is not None else "")
                elif field == "wn_validation_status":
                    value = getattr(observation, "wn_validation_status", "")
                    row_data.append(str(value) if value is not None else "")
                elif field == "wn_cluster_id":
                    value = getattr(observation, "wn_cluster_id", "")
                    row_data.append(str(value) if value is not None else "")
                else:
                    value = getattr(observation, field, "")
                    row_data.append(str(value) if value is not None else "")
            except Exception as e:
                logger.warning(f"Error processing field {field}: {str(e)}")
                row_data.append("")
        return row_data
    except Exception as e:
        logger.error(f"Error preparing row data: {str(e)}")
        return [""] * len(PUBLIC_FIELDS)

def generate_rows(
    queryset: QuerySet[Model],
    writer: WriterProtocol,
    is_admin: bool,
    user_municipality_ids: Set[str],
    batch_size: int = 200
) -> Iterator[Any]:
    """Generate CSV rows for streaming with memory optimization."""
    yield writer.writerow(PUBLIC_FIELDS)

    for observation in queryset.iterator(chunk_size=batch_size):
        try:
            row = prepare_row_data(
                observation, 
                is_admin, 
                user_municipality_ids
            )
            yield writer.writerow(row)
        except Exception as e:
            logger.error(f"Error processing observation {observation.id}: {e}")
            continue

def generate_csv_to_s3(queryset: Any, file_path: str, is_admin: bool = True, user_municipality_ids: Set[int] = set()) -> None:
    """Generate a CSV file and save it to S3."""
    logger.info(f"Generating CSV and saving to S3 at: {file_path}")
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    
    # Generate rows
    rows = generate_rows(queryset, writer, is_admin, user_municipality_ids)
    for row in rows:
        writer.writerow(row)
    
    # Save to S3
    buffer.seek(0)
    try:
        default_storage.save(file_path, io.StringIO(buffer.getvalue()))
        logger.info(f"Successfully saved CSV to S3: {file_path}")
    except Exception as e:
        logger.error(f"Failed to save CSV to S3 at {file_path}: {str(e)}")
        raise
    finally:
        buffer.close()
        
@shared_task(
    name="generate_export",
    max_retries=3,
    default_retry_delay=60,
    soft_time_limit=1700,
    time_limit=1800,
    acks_late=True
)
def generate_export(export_id: int, filters: Dict[str, Any], user_id: Optional[int] = None) -> Dict[str, Any]:
    """Generate CSV export of observations based on filters and save to S3."""
    logger.info(f"Starting export {export_id} for user {user_id} with filters: {filters}")
    export = Export.objects.get(id=export_id)

    try:
        # Update export status
        export.status = 'processing'
        export.save()

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
        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers
        writer.writerow(PUBLIC_FIELDS)

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
            
            for observation in batch:
                try:
                    row = prepare_row_data(observation, is_admin, user_municipality_ids)
                    writer.writerow(row)
                    processed += 1
                    
                    if processed % 100 == 0:
                        progress = int((processed / initial_count) * 100)
                        export.progress = progress
                        export.save()
                        logger.info(f"Processed {processed}/{initial_count} records")
                except Exception as e:
                    logger.error(f"Error processing observation {observation.id}: {e}")
                    continue

        # Save to S3
        file_path = f"VESPADB/EXPORT/export_{export_id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        default_storage.save(file_path, io.StringIO(output.getvalue()))
        output.close()

        # Update export record
        export.status = 'completed'
        export.file_path = file_path
        export.completed_at = timezone.now()
        export.progress = 100
        export.save()

        logger.info(f"Export {export_id} completed successfully and saved to S3 at {file_path}")
        return {
            'status': 'completed',
            'file_path': file_path,
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
        # Delete file from S3 if exists
        if export.file_path:
            try:
                default_storage.delete(export.file_path)
                logger.info(f"Deleted S3 file for export {export.id}: {export.file_path}")
            except Exception as e:
                logger.error(f"Failed to delete S3 file for export {export.id}: {str(e)}")
        
        # Delete the export record
        export.delete()
        logger.info(f"Cleaned up export {export.id}")
        
@shared_task(
    name="generate_hourly_export",
    max_retries=3,
    default_retry_delay=60,
    soft_time_limit=1700,
    time_limit=1800,
    acks_late=True
)
def generate_hourly_export() -> Dict[str, Any]:
    """Generate a CSV export of all observations hourly and save to S3, deleting the previous file."""
    logger.info("Starting hourly export of all observations")
    
    try:
        # Get all observations with optimized query
        queryset = (Observation.objects
                   .all()
                   .select_related("province", "municipality", "reserved_by")
                   .order_by("id"))
        
        initial_count = queryset.count()
        logger.info(f"Total observations to export: {initial_count}")

        # Generate file path with timestamp
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        new_file_path = f"VESPADB/EXPORT/observations_{timestamp}.csv"

        # List existing files in S3 export directory
        previous_files = default_storage.listdir("VESPADB/EXPORT/")[1]  # Get files only
        previous_files = [f for f in previous_files if f.startswith("observations_") and f.endswith(".csv")]
        
        # Generate and save new CSV to S3 using batch processing for memory efficiency
        generate_csv_to_s3(queryset, new_file_path, is_admin=True)

        # Delete previous files - keep at most the 2 most recent previous files as backup
        # Sort files by name (which includes timestamp)
        if len(previous_files) > 2:
            files_to_delete = sorted(previous_files)[:-2]
            for old_file in files_to_delete:
                old_file_path = f"VESPADB/EXPORT/{old_file}"
                try:
                    default_storage.delete(old_file_path)
                    logger.info(f"Deleted previous export file: {old_file_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete previous export file {old_file_path}: {str(e)}")

        logger.info(f"Hourly export completed successfully: {new_file_path}")
        return {
            "status": "completed",
            "file_path": new_file_path,
            "total_processed": initial_count
        }

    except Exception as e:
        logger.exception(f"Hourly export failed: {str(e)}")
        return {"status": "failed", "error": str(e)}

def get_latest_hourly_export() -> str:
    """Get the file path of the latest hourly export."""
    try:
        # List existing files in S3 export directory
        export_files = default_storage.listdir("VESPADB/EXPORT/")[1]  # Get files only
        hourly_files = [f for f in export_files if f.startswith("observations_") and f.endswith(".csv")]
        
        if not hourly_files:
            logger.warning("No hourly export files found")
            return None
            
        # Sort by name (which includes timestamp) to get the latest
        latest_file = sorted(hourly_files, reverse=True)[0]
        return f"VESPADB/EXPORT/{latest_file}"
    except Exception as e:
        logger.error(f"Error finding latest hourly export: {str(e)}")
        return None
