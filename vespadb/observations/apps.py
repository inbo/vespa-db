"""Config for observations app."""

from django.apps import AppConfig


class ObservationsConfig(AppConfig):
    """Config for observations app."""

    name = "vespadb.observations"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        """Import signals when the app is ready."""
        import vespadb.observations.signals  # noqa: F401, PLC0415
