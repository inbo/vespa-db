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
                        # Remove microseconds and tzinfo for export consistency
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
                elif field == "eradication_date":
                    date_val = getattr(observation, "eradication_date", None)
                    row_data.append(date_val.isoformat() if date_val else "")
                elif field == "eradication_result":
                    value = getattr(observation, "eradication_result", "")
                    row_data.append(str(value) if value is not None else "")
                elif field == "images":
                    value = getattr(observation, "images", [])
                    if isinstance(value, list):
                        if not value:
                            row_data.append("")
                        elif len(value) == 1:
                            # One image → export URL without quotes
                            row_data.append(value[0])
                        else:
                            # Multiple images → join with commas (no spaces) and enclose in double quotes
                            joined = ",".join(value)
                            row_data.append(f'"{joined}"')
                    else:
                        # In case the field is stored as a string that looks like a list
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
                                row_data.append(f'"{joined}"')
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
