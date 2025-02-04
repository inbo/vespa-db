from typing import Iterator, List, Set, Any, Union, Protocol
from django.db.models.query import QuerySet
from django.db.models import Model
import csv
import logging
from ..models import Observation

logger = logging.getLogger(__name__)

class WriterProtocol(Protocol):
    def writerow(self, row: List[str]) -> Any: ...

PUBLIC_FIELDS = [
    "id", "created_datetime", "latitude", "longitude", "source",
    "nest_height", "nest_size", "nest_location", "nest_type",
    "observation_datetime", "province", "municipality", "nest_status",
    "source_id", "anb_domain"
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
    """
    Prepare a single row of data for the CSV export with error handling.
    """
    try:
        allowed_fields = PUBLIC_FIELDS 
        
        row_data: List[str] = []
        for field in PUBLIC_FIELDS:
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
                        datetime_val = datetime_val.replace(microsecond=0, tzinfo=None)
                        row_data.append(datetime_val.strftime("%Y-%m-%dT%H:%M:%SZ"))
                    else:
                        row_data.append("")
                elif field == "province":
                    row_data.append(observation.province.name if observation.province else "")
                elif field == "municipality":
                    row_data.append(observation.municipality.name if observation.municipality else "")
                elif field == "nest_status":
                    row_data.append(get_status(observation))
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
