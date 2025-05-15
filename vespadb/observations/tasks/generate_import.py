import json
import csv
import io
from typing import Dict, Any
from celery import shared_task
from django.utils import timezone
from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import Q
from django.utils.timezone import now
from vespadb.observations.models import Import, Observation
from vespadb.users.utils import get_import_user
from vespadb.users.models import UserType
import logging

logger = logging.getLogger(__name__)

@shared_task(
    name="process_import",
    max_retries=3,
    default_retry_delay=60,
    soft_time_limit=1700,
    time_limit=1800,
    acks_late=True
)
def process_import(import_id: int) -> Dict[str, Any]:
    """Process an asynchronous import of observations from a JSON or CSV file."""
    logger.info(f"Starting import {import_id}")
    import_record = Import.objects.get(id=import_id)

    try:
        import_record.status = "processing"
        import_record.save()

        # Read file from S3
        file_path = import_record.file_path
        logger.info(f"Reading file from S3: {file_path}")
        file = default_storage.open(file_path)
        content_type = "application/json" if file_path.endswith(".json") else "text/csv"
        data = []

        if content_type == "application/json":
            try:
                data = json.load(file)
                logger.debug(f"JSON data loaded: {json.dumps(data, indent=2)[:1000]}...")  # Truncate for brevity
            except json.JSONDecodeError as e:
                logger.exception(f"Invalid JSON format in file {file_path}")
                import_record.status = "failed"
                import_record.error_message = f"Invalid JSON format: {str(e)}"
                import_record.save()
                return {"status": "failed", "error": str(e)}
        else:
            file.seek(0)
            reader = csv.DictReader(io.StringIO(file.read().decode("utf-8")))
            data = [row for row in reader]
            logger.debug(f"CSV data loaded: {data[:2]}...")  # Log first two rows for debugging

        logger.info(f"Loaded {len(data)} records from {file_path}")

        # Initialize ObservationsViewSet for processing
        from vespadb.observations.views import ObservationsViewSet
        viewset = ObservationsViewSet()
        viewset.request = None  # No request context needed for task

        # Process data
        logger.info(f"Processing {len(data)} records")
        processed_data, errors = viewset.process_data(data)
        if errors:
            logger.error(f"Data validation errors for import {import_id}: {errors}")
            import_record.status = "failed"
            import_record.error_message = json.dumps(errors)
            import_record.save()
            default_storage.delete(file_path)  # Delete file on error
            return {"status": "failed", "errors": errors}

        # Save observations
        import_user = get_import_user(UserType.IMPORT)
        created_ids = []
        updated_ids = []

        with transaction.atomic():
            for i, data in enumerate(processed_data, 1):
                wn_id = data.get("wn_id")
                source = data.get("source")
                source_id = data.get("source_id")
                observation_id = data.pop("id", None)
                logger.debug(f"Processing record {i}/{len(processed_data)} (wn_id={wn_id}, id={observation_id})")

                # Case 1: ID is provided
                if observation_id:
                    try:
                        obs = Observation.objects.get(id=observation_id)
                        logger.info(f"Updating observation {observation_id} (wn_id={wn_id})")
                        for field, value in data.items():
                            setattr(obs, field, value)
                        obs.modified_by = import_user
                        obs.modified_datetime = now()
                        obs.save()
                        updated_ids.append(obs.id)
                        logger.info(f"Updated observation {obs.id} (wn_id={wn_id})")
                    except Observation.DoesNotExist:
                        error_msg = f"Observation with id {observation_id} does not exist"
                        logger.error(error_msg)
                        errors.append({"record": i, "error": error_msg})
                        continue
                # Case 2: No ID provided
                else:
                    # Validate that wn_id/source or source_id/source is provided
                    has_wn_id_source = wn_id is not None and source is not None
                    has_source_id_source = source_id is not None and source is not None
                    if not (has_wn_id_source or has_source_id_source):
                        error_msg = "Either wn_id/source or source_id/source combination is required when no id is provided"
                        logger.error(error_msg)
                        errors.append({"record": i, "error": error_msg})
                        continue

                    # Check for existing observation with wn_id/source or source_id/source
                    query = Q()
                    if has_wn_id_source:
                        query |= Q(wn_id=wn_id, source=source)
                    if has_source_id_source:
                        query |= Q(source_id=source_id, source=source)
                    
                    existing_obs = Observation.objects.filter(query).first()
                    if existing_obs:
                        error_msg = (
                            f"Observation with wn_id={wn_id}/source={source} "
                            f"or source_id={source_id}/source={source} already exists (id={existing_obs.id})"
                        )
                        logger.error(error_msg)
                        errors.append({"record": i, "error": error_msg})
                        continue

                    # Create new observation
                    logger.info(f"Creating new observation (wn_id={wn_id}, source_id={source_id})")
                    data["created_by"] = import_user
                    data["modified_by"] = import_user
                    try:
                        obs = Observation.objects.create(**data)
                        created_ids.append(obs.id)
                        logger.info(f"Created observation {obs.id} (wn_id={wn_id})")
                    except Exception as e:
                        error_msg = f"Failed to create observation: {str(e)}"
                        logger.error(error_msg)
                        errors.append({"record": i, "error": error_msg})
                        continue

                import_record.progress = int((len(created_ids) + len(updated_ids)) / len(processed_data) * 100)
                import_record.save()

        # Handle errors
        if errors:
            logger.error(f"Import {import_id} failed due to validation errors: {errors}")
            import_record.status = "failed"
            import_record.error_message = json.dumps(errors)
            import_record.save()
            default_storage.delete(file_path)
            return {"status": "failed", "errors": errors}

        # Update import record
        import_record.status = "completed"
        import_record.completed_at = timezone.now()
        import_record.created_ids = created_ids
        import_record.updated_ids = updated_ids
        import_record.save()

        # Delete the file from S3
        try:
            default_storage.delete(file_path)
            logger.info(f"Deleted file from S3: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to delete file {file_path} from S3: {str(e)}")

        logger.info(f"Import {import_id} completed successfully: {len(created_ids)} created, {len(updated_ids)} updated")
        return {
            "status": "completed",
            "created_ids": created_ids,
            "updated_ids": updated_ids,
        }
    except Exception as e:
        logger.exception(f"Import {import_id} failed: {str(e)}")
        import_record.status = "failed"
        import_record.error_message = str(e)
        import_record.save()
        # Delete the file from S3 on failure
        try:
            default_storage.delete(file_path)
            logger.info(f"Deleted file from S3: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to delete file {file_path} from S3: {str(e)}")
        return {"status": "failed", "error": str(e)}

@shared_task
def cleanup_old_imports():
    logger.info("Starting cleanup of old imports")
    cutoff = timezone.now() - timezone.timedelta(days=7)  # Keep imports for 7 days
    old_imports = Import.objects.filter(created_at__lt=cutoff)
    for import_record in old_imports:
        import_record.delete()
        logger.info(f"Cleaned up import {import_record.id}")
