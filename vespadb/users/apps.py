"""VespaDB Users App Configurations."""

from contextlib import suppress

from django.apps import AppConfig
from django.db.utils import IntegrityError


class UsersConfig(AppConfig):
    """VespaDB Users App Configurations."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "vespadb.users"

    def ready(self) -> None:
        """Create System Users if they don't exist yet.

        Every time Django application starts, Django will execute the ready method.
        """
        from vespadb.users.models import UserType, VespaUser  # noqa: PLC0415

        for user_type in [UserType.SYNC, UserType.IMPORT]:
            with suppress(IntegrityError):
                VespaUser.objects.get_or_create(username=user_type.value, defaults={"user_type": user_type.value})
