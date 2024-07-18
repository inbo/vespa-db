"""."""

import logging
from enum import Enum

from django.contrib.auth.models import AbstractUser
from django.db import models

from vespadb.observations.models import Municipality

logger = logging.getLogger(__name__)


class UserType(Enum):
    """User Type Enum."""

    REGULAR = "regular"
    SYNC = "sync"
    IMPORT = "import"

    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        """Return choices for the enum."""
        return [(key.value, key.name) for key in cls]


class VespaUser(AbstractUser):
    """Model for the Vespa user."""

    user_type = models.CharField(
        max_length=10,
        choices=UserType.choices(),
        default=UserType.REGULAR.value,
    )
    personal_data_access = models.BooleanField(default=False)
    municipalities = models.ManyToManyField(
        Municipality,
        blank=True,
        related_name="users",
    )
    reservation_count = models.IntegerField(default=0)
