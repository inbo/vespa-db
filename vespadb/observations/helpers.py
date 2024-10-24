"""Observation helpers."""

import time
from collections.abc import Callable
from datetime import datetime
from typing import Any, TypeVar

import pytz
from dateutil import parser
from django.db.utils import OperationalError

# List of accepted datetime formats
DATETIME_FORMATS = [
    "%Y-%m-%dT%H:%M:%S.%fZ",
    "%Y-%m-%dT%H:%M:%S.%f%z",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
]

T = TypeVar("T")


def parse_and_convert_to_utc(datetime_str: str) -> datetime:
    """
    Parse a datetime string and convert it to UTC.

    Args:
        datetime_str (str): The datetime string to convert.

    Returns
    -------
        datetime: The converted UTC datetime.
    """
    for _fmt in DATETIME_FORMATS:
        try:
            parsed_datetime = parser.parse(datetime_str)
            if parsed_datetime.tzinfo is None:
                local_tz = pytz.timezone("Europe/Brussels")
                parsed_datetime = local_tz.localize(parsed_datetime)
            return parsed_datetime.astimezone(pytz.UTC)
        except ValueError:
            continue
    raise ValueError(f"Invalid datetime format: {datetime_str}")


def parse_and_convert_to_cet(datetime_str: str) -> datetime:
    """
    Convert a UTC datetime to CET.

    Args:
        dt (datetime): The UTC datetime to convert.

    Returns
    -------
        datetime: The converted CET datetime.
    """
    cet_tz = pytz.timezone("Europe/Brussels")
    return parser.parse(datetime_str).astimezone(cet_tz)


def retry_with_backoff(func: Callable[..., T], retries: int=3, backoff_in_seconds: int=2) -> Any:
    """Retry mechanism for retrying a function with a backoff strategy."""
    for attempt in range(retries):
        try:
            return func()
        except Exception as e:
            if attempt < retries - 1:
                wait_time = backoff_in_seconds * (2 ** attempt)
                time.sleep(wait_time)
            else:
                raise