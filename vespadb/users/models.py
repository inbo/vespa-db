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

class TermsOfServiceAcceptance(models.Model):
    """
    Model to track when a user has accepted the terms of service
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='terms_acceptances'
    )
    accepted_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-accepted_at']
        verbose_name = 'Terms of Service Acceptance'
        verbose_name_plural = 'Terms of Service Acceptances'
        
    def __str__(self):
        return f"{self.user.username} - {self.accepted_at.strftime('%Y-%m-%d %H:%M:%S')}"
