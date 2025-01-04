from typing import Iterator, List, Set, Any, Union, Protocol
from django.db.models.query import QuerySet
from django.db.models import Model
import csv
import logging
from ..models import Observation

logger = logging.getLogger(__name__)

class WriterProtocol(Protocol):
    def writerow(self, row: List[str]) -> Any: ...

CSV_HEADERS = [
    "id", "created_datetime", "modified_datetime", "latitude", "longitude", 
    "source", "source_id", "nest_height", "nest_size", "nest_location", 
    "nest_type", "observation_datetime", "province", "eradication_date", 
    "municipality", "images", "anb_domain", "notes", "eradication_result", 
    "wn_id", "wn_validation_status", "nest_status"
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
        # Determine allowed fields based on permissions
        if is_admin or (observation.municipality_id in user_municipality_ids):
            allowed_fields = CSV_HEADERS
        else:
            allowed_fields = ["id", "created_datetime", "latitude", "longitude", "source",
                            "nest_height", "nest_type", "observation_datetime", "province",
                            "municipality", "nest_status", "source_id", "anb_domain"]
        
        row_data: List[str] = []
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

def generate_rows(
    queryset: QuerySet[Model],
    writer: WriterProtocol,
    is_admin: bool,
    user_municipality_ids: Set[str]
) -> Iterator[Any]:
    """
    Generate CSV rows for streaming.
    """
    # First yield the headers
    yield writer.writerow(CSV_HEADERS)

    # Then yield the data rows
    for observation in queryset.iterator(chunk_size=2000):
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
