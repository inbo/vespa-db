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
    "anb",
    "nest_status",
    "eradication_date",
    "eradication_result",
    "images",
    "nest_type",
    "nest_location",
    "nest_height",
    "nest_size",
    "queen_present",
    "moth_present",
    "duplicate_nest",
    "other_species_nest",
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
    if observation.eradication_result == 'successful':
        return "eradicated"
    if observation.eradication_result is not None:
        return "visited"
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
) -> Iterator[List[str]]:
    """Generate CSV rows for streaming with memory optimization."""
    yield PUBLIC_FIELDS  # just yield the header row

    for observation in queryset.iterator(chunk_size=batch_size):
        try:
            row = prepare_row_data(
                observation, 
                is_admin, 
                user_municipality_ids
            )
            yield row
        except Exception as e:
            logger.error(f"Error processing observation {observation.id}: {e}")
            continue

def generate_csv_to_s3(queryset: Any, file_path: str, is_admin: bool = True, user_municipality_ids: Set[int] = set()) -> None:
    logger.info(f"Generating CSV and saving to S3 at: {file_path}")
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    
    try:
        for row in generate_rows(queryset, writer, is_admin, user_municipality_ids):
            writer.writerow(row)

        buffer.seek(0)
        default_storage.save(file_path, io.StringIO(buffer.getvalue()))
        logger.info(f"Successfully saved CSV to S3: {file_path}")
    except Exception as e:
        logger.error(f"Failed to save CSV to S3 at {file_path}: {str(e)}")
        raise
    finally:
        buffer.close() 

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
    name='vespadb.observations.tasks.generate_export.generate_hourly_export',
    max_retries=3,
    default_retry_delay=60,
    soft_time_limit=1700,
    time_limit=1800,
    acks_late=True
)
def generate_hourly_export() -> Dict[str, Any]:
    """Generate a CSV export of all observations hourly and save to S3, deleting old files."""
    logger.info("Starting hourly export of all observations")
    
    try:
        # Get all observations with optimized query
        queryset = (Observation.objects
                   .filter(visible=True)
                   .select_related("province", "municipality", "reserved_by")
                   .order_by("id"))
        
        initial_count = queryset.count()
        logger.info(f"Total observations to export: {initial_count}")

        # Generate file path with timestamp
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        new_file_path = f"VESPADB/EXPORT/observations_{timestamp}.csv"

        # List existing files in S3 export directory
        try:
            dirs, files = default_storage.listdir("VESPADB/EXPORT/")
            previous_files = [f for f in files if f.startswith("observations_") and f.endswith(".csv")]
        except FileNotFoundError:
            logger.info("Export directory doesn't exist yet, will be created")
            previous_files = []
        except Exception as e:
            logger.warning(f"Could not list existing files: {str(e)}")
            previous_files = []
        
        # Generate and save new CSV to S3 using batch processing for memory efficiency
        generate_csv_to_s3(queryset, new_file_path, is_admin=True)

        # Clean up old files - keep only the 2 most recent files as backup
        if len(previous_files) > 2:
            files_to_delete = sorted(previous_files)[:-2]  # Keep the 2 most recent
            for old_file in files_to_delete:
                old_file_path = f"VESPADB/EXPORT/{old_file}"
                try:
                    default_storage.delete(old_file_path)
                    logger.info(f"Deleted old export file: {old_file_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete old export file {old_file_path}: {str(e)}")

        # Update any pending Export records that might be waiting for this file
        pending_exports = Export.objects.filter(status='pending', file_path__isnull=True)
        for export in pending_exports:
            export.file_path = new_file_path
            export.status = 'completed'
            export.completed_at = timezone.now()
            export.progress = 100
            export.save()
            logger.info(f"Updated pending export record {export.id}")

        logger.info(f"Hourly export completed successfully: {new_file_path}")
        return {
            "status": "completed",
            "file_path": new_file_path,
            "total_processed": initial_count
        }

    except Exception as e:
        logger.exception(f"Hourly export failed: {str(e)}")
        
        # Update any pending Export records to failed status
        pending_exports = Export.objects.filter(status='pending', file_path__isnull=True)
        for export in pending_exports:
            export.status = 'failed'
            export.error_message = str(e)
            export.save()
        
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
