"""Observation models for the observations app."""

from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.db import models
from django.utils.translation import gettext_lazy as _


class NestHeightEnum(models.TextChoices):
    """Enum for the height of the nest."""

    BELOW_4_METERS = "lager_dan_4_meter", _("Lager dan 4 meter")
    ABOVE_4_METERS = "hoger_dan_4_meter", _("Hoger dan 4 meter")


class NestSizeEnum(models.TextChoices):
    """Enum for the size of the nest."""

    LESS_THAN_25_CM = "minder_dan_25_cm", _("Minder dan 25 cm")
    MORE_THAN_25_CM = "meer_dan_25_cm", _("Meer dan 25 cm")


class NestLocationEnum(models.TextChoices):
    """Enum for the location of the nest."""

    OUTSIDE_UNCOVERED_BUILDING = "buiten_onbedekt_op_gebouw", _("Buiten, onbedekt op gebouw")
    OUTSIDE_UNCOVERED_TREE = "buiten_onbedekt_in_boom_of_struik", _("Buiten, onbedekt in boom of struik")
    OUTSIDE_COVERED_BY_CONSTRUCTION = (
        "buiten_maar_overdekt_door_constructie",
        _("Buiten, maar overdekt door constructie"),
    )
    OUTSIDE_NATURALLY_COVERED = "buiten_natuurlijk_overdekt", _("Buiten, natuurlijk overdekt")
    INSIDE_BUILDING = "binnen_in_gebouw_of_constructie", _("Binnen, in gebouw of constructie")
    UNKNOWN = "onbekend", _("Onbekend")


class NestTypeEnum(models.TextChoices):
    """Enum for the type of the nest."""

    ACTIVE_EMBRYONAL_NEST = "AH_actief_embryonaal_nest", _("AH - actief embryonaal nest")
    ACTIVE_PRIMARY_NEST = "AH_actief_primair_nest", _("AH - actief primair nest")
    ACTIVE_SECONDARY_NEST = "AH_actief_secundair_nest", _("AH - actief secundair nest")
    INACTIVE_EMPTY_NEST = "AH_inactief_leeg_nest", _("AH - inactief/leeg nest")
    POTENTIAL_NEST = "AH_potentieel_nest", _("AH - potentieel nest (meer info nodig)")
    NEST_OTHER_SPECIES = "nest_andere_soort", _("Nest andere soort")
    NO_NEST = "geen_nest", _("Geen nest (object, insect)")


class EradicationResultEnum(models.TextChoices):
    """Enum for the result of the eradication."""

    SUCCESSFUL = "successful", _("Succesvol behandeld")
    UNSUCCESSFUL = "unsuccessful", _("Niet succesvol behandeld")
    UNTREATED = "untreated", _("Niet behandeld")
    UNKNOWN = "unknown", _("Onbekend")


class EradicationProductEnum(models.TextChoices):
    """Enum for the product used for the eradication."""

    PERMAS_D = "Permas-D", _("Permas-D")
    LIQUID_NITROGEN = "vloeibare_stikstof", _("Vloeibare stikstof")
    VESPA_FICAM_D = "Vespa_Ficam_D", _("Vespa Ficam D")
    TOPSCORE_PAL = "Topscore_PAL", _("Topscore PAL")
    ETHER_ACETONE_ETHYL_ACETATE = "ether_aceton_ethyl_acetate", _("Ether/aceton/ethyl acetate")
    DIATOMACEOUS_EARTH = "diatomeeenaarde", _("Diatomeënaarde")
    OTHER = "andere", _("Andere")
    NONE = "geen", _("Geen")
    UNKNOWN = "onbekend", _("Onbekend")


class Observation(models.Model):
    """Model for the observation of a Vespa velutina nest."""

    id = models.AutoField(primary_key=True)
    wn_id = models.IntegerField(unique=True)
    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)
    location = gis_models.PointField()
    source = models.CharField(max_length=255)
    wn_notes = models.TextField(blank=True, null=True)
    wn_admin_notes = models.TextField(blank=True, null=True)
    species = models.IntegerField()
    nest_height = models.CharField(max_length=50, choices=NestHeightEnum)
    nest_size = models.CharField(max_length=50, choices=NestSizeEnum)
    nest_location = models.CharField(max_length=50, choices=NestLocationEnum)
    nest_type = models.CharField(max_length=50, choices=NestTypeEnum)
    observer_phone_number = models.CharField(max_length=20, blank=True, null=True)
    observer_email = models.EmailField(blank=True, null=True)
    observer_name = models.CharField(max_length=255, blank=True, null=True)
    observer_allows_contact = models.BooleanField(default=False)
    observation_datetime = models.DateTimeField()
    wn_cluster_id = models.IntegerField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="created_observations", on_delete=models.SET_NULL, null=True
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="modified_observations", on_delete=models.SET_NULL, null=True
    )
    eradication_datetime = models.DateTimeField(blank=True, null=True)
    eradicator_name = models.CharField(max_length=255, blank=True, null=True)
    eradication_result = models.CharField(max_length=50, choices=EradicationResultEnum)
    eradication_product = models.CharField(max_length=50, choices=EradicationProductEnum, blank=True, null=True)
    eradication_notes = models.TextField(blank=True, null=True)
    wn_modified_datetime = models.DateTimeField(blank=True, null=True)
    wn_created_datetime = models.DateTimeField(blank=True, null=True)
    duplicate = models.BooleanField(default=False)
    images = models.JSONField(default=list)

    def __str__(self) -> str:
        """Return the string representation of the model."""
        return f"Observation {self.id} - location: {self.location} - eradicated: {self.eradication_datetime}"


class Municipality(models.Model):
    """Model for the municipalities."""

    name = models.CharField(max_length=255)
    nis_code = models.CharField(max_length=255)
    polygon = gis_models.MultiPolygonField()

    def __str__(self) -> str:
        """Return the string representation of the model."""
        return str(self.name)
