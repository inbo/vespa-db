import logging
from enum import Enum

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db import models
from django.conf import settings
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
    municipalities = models.ManyToManyField(
        Municipality,
        blank=True,
        related_name="users",
    )
    reservation_count = models.IntegerField(default=0)

    def has_assigned_municipality(self) -> bool:
        """Check if user has assigned municipalities."""
        return bool(self.municipalities.exists())

    def get_permission_level(self) -> str:
        """Return the permission level based on user's assigned municipalities."""
        if self.is_superuser:
            return "admin"
        elif self.has_assigned_municipality():
            return "logged_in_with_municipality"
        else:
            return "logged_in_without_municipality"
