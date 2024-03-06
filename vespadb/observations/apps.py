"""Config for observations app."""

from django.apps import AppConfig


class ObservationsConfig(AppConfig):
    """Config for observations app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "vespadb.observations"
    
    def ready(self) -> None:
        """Import signals."""
        import vespadb.observations.signals
