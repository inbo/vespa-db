"""Observation models for the observations app."""

import logging
from typing import Any

from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.db import models
from django.utils.translation import gettext_lazy as _

from vespadb.observations.utils import check_if_point_in_anb_area, get_municipality_from_coordinates

logger = logging.getLogger(__name__)


class NestHeightEnum(models.TextChoices):
    """Enum for the height of the nest."""

    BELOW_4_METERS = "lager_dan_4_meter", _("Lager dan 4 meter")
    ABOVE_4_METERS = "hoger_dan_4_meter", _("Hoger dan 4 meter")


class NestSizeEnum(models.TextChoices):
    """Enum for the size of the nest."""

    LESS_THAN_25_CM = "kleiner_dan_25_cm", _("Kleiner dan 25 cm")
    MORE_THAN_25_CM = "groter_dan_25_cm", _("Groter dan 25 cm")


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


class NestTypeEnum(models.TextChoices):
    """Enum for the type of the nest."""

    ACTIVE_EMBRYONAL_NEST = "actief_embryonaal_nest", _("actief embryonaal nest")
    ACTIVE_PRIMARY_NEST = "actief_primair_nest", _("actief primair nest")
    ACTIVE_SECONDARY_NEST = "actief_secundair_nest", _("actief secundair nest")
    INACTIVE_EMPTY_NEST = "inactief_leeg_nest", _("inactief/leeg nest")
    POTENTIAL_NEST = "potentieel_nest", _("potentieel nest")


class EradicationResultEnum(models.TextChoices):
    """Enum for the result of the eradication."""

    SUCCESSFUL = "successful", _("Succesvol behandeld")
    UNSUCCESSFUL = "unsuccessful", _("Niet succesvol behandeld")
    UNTREATED = "untreated", _("Niet behandeld")
    UNKNOWN = "unknown", _("Onbekend")


class ValidationStatusEnum(models.TextChoices):
    """Enum for the result of the eradication."""

    UNKNOWN = "onbekend", _("Unknown")
    APPROVED_WITH_EVIDENCE = "goedgekeurd_met_bewijs", _("Approved (with evidence)")
    APPROVED_BY_ADMIN = "goedgekeurd_door_admin", _("Approved (by admin)")
    APPROVED_AUTOMATIC_VALIDATION = "goedgekeurd_automatische_validatie", _("Approved (automatic validation)")
    IN_PROGRESS = "in_behandeling", _("In progress")
    REJECTED = "afgewezen", _("Rejected")
    NOT_EVALUABLE_YET = "nog_niet_te_beoordelen", _("Not evaluable yet")


class EradicationMethodEnum(models.TextChoices):
    """Enum for the result of the eradication."""

    FREEZER = "diepvries", _("Diepvries")
    TELESCOPIC_STEM = "telescoopsteel", _("Telescoopsteel")
    LOCKABLE_JAR_BOX = "afsluitbaar potje/doos", _("Afsluitbaar potje/doos")
    LIQUID_SPRAYER = "vloeistofverstuiver", _("Vloeistofverstuiver")
    POWDER_SPRAYER = "poederverstuiver", _("Poederverstuiver")


class EradicationAfterCareEnum(models.TextChoices):
    """Enum for the result of the eradication."""

    NEST_FULLY_REMOVED = (
        "nest_volledig_verwijderd",
        _("Nest volledig verwijderd"),
    )
    NEST_PARTIALLY_REMOVED = (
        "nest_gedeeltelijk_verwijderd",
        _("Nest gedeeltelijk verwijderd"),
    )
    NEST_LEFT_HANGING = (
        "nest_laten_hangen",
        _("Nest laten hangen"),
    )


class EradicationProblemsEnum(models.TextChoices):
    """Enum for the result of the eradication."""

    STINGING = (
        "stinging",
        _("Steken"),
    )
    NEST_FALLING = (
        "nest_falling",
        _("Nest gevallen"),
    )
    DIZZINESS = (
        "dizziness",
        _("Duizeligheid"),
    )
    POISON_PROJECTION = (
        "poison_projection",
        _("Gif projectie"),
    )


class EradicationProductEnum(models.TextChoices):
    """Enum for the product used for the eradication."""

    PERMAS_D = "Permas-D", _("Permas-D")
    LIQUID_NITROGEN = "vloeibare_stikstof", _("Vloeibare stikstof")
    VESPA_FICAM_D = "Vespa_Ficam_D", _("Vespa Ficam D")
    TOPSCORE_PAL = "Topscore_PAL", _("Topscore PAL")
    ETHER_ACETONE_ETHYL_ACETATE = "ether_aceton_ethyl_acetate", _("Ether/aceton/ethyl acetate")
    DIATOMACEOUS_EARTH = "diatomeeënaarde", _("Diatomeeënaarde")
    OTHER = "andere", _("Andere")


class Province(models.Model):
    """Model voor de Belgische gemeenten met uitgebreide gegevens."""

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    nis_code = models.CharField(max_length=255)
    polygon = gis_models.MultiPolygonField(srid=31370)

    oidn = models.BigIntegerField(blank=True, null=True)
    uidn = models.BigIntegerField(blank=True, null=True)
    terrid = models.BigIntegerField(blank=True, null=True)
    length = models.FloatField(blank=True, null=True)
    surface = models.FloatField(blank=True, null=True)

    def __str__(self) -> str:
        """Return the string representation of the model."""
        return str(self.name)


class Municipality(models.Model):
    """Model voor de Belgische gemeenten met uitgebreide gegevens."""

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    nis_code = models.CharField(max_length=255)
    polygon = gis_models.MultiPolygonField(srid=31370)

    oidn = models.BigIntegerField(blank=True, null=True)
    uidn = models.BigIntegerField(blank=True, null=True)
    terrid = models.BigIntegerField(blank=True, null=True)
    datpublbs = models.DateField(blank=True, null=True)
    numac = models.CharField(max_length=10, blank=True, null=True)
    length = models.FloatField(blank=True, null=True)
    surface = models.FloatField(blank=True, null=True)
    province = models.ForeignKey(
        Province, on_delete=models.SET_NULL, null=True, blank=True, related_name="municipalities"
    )

    def __str__(self) -> str:
        """Return the string representation of the model."""
        return str(self.name)


class ANB(models.Model):
    """Model for the Agentschap voor Natuur en Bos (ANB) domain with detailed data."""

    id = models.AutoField(primary_key=True)
    domain = models.CharField(max_length=255)
    province = models.CharField(max_length=255)
    regio = models.CharField(max_length=255, null=True)
    liberties = models.CharField(max_length=255, null=True)
    administrator = models.CharField(max_length=255, null=True)
    contact = models.EmailField(max_length=255, null=True)
    polygon = gis_models.MultiPolygonField(srid=31370)

    def __str__(self) -> str:
        """Return the string representation of the model."""
        return str(self.domain)


class Observation(models.Model):
    """Model for the observation of a Vespa velutina nest."""

    id = models.AutoField(primary_key=True)
    wn_id = models.IntegerField(unique=True)
    created_datetime = models.DateTimeField(auto_now_add=True)
    modified_datetime = models.DateTimeField(auto_now=True)
    location = gis_models.PointField()
    source = models.CharField(max_length=255, blank=True, null=True)

    wn_notes = models.TextField(blank=True, null=True)
    wn_admin_notes = models.TextField(blank=True, null=True)
    wn_validation_status = models.CharField(max_length=50, choices=ValidationStatusEnum, blank=True, null=True)

    species = models.IntegerField()
    nest_height = models.CharField(max_length=50, choices=NestHeightEnum, blank=True, null=True)
    nest_size = models.CharField(max_length=50, choices=NestSizeEnum, blank=True, null=True)
    nest_location = models.CharField(max_length=50, choices=NestLocationEnum, blank=True, null=True)
    nest_type = models.CharField(max_length=50, choices=NestTypeEnum, blank=True, null=True)

    observer_phone_number = models.CharField(max_length=20, blank=True, null=True)
    observer_email = models.EmailField(blank=True, null=True)
    observer_name = models.CharField(max_length=255, blank=True, null=True)
    observer_allows_contact = models.BooleanField(default=False)
    observation_datetime = models.DateTimeField()

    wn_cluster_id = models.IntegerField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="modified_observations", on_delete=models.SET_NULL, null=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="created_observations", on_delete=models.SET_NULL, null=True
    )
    wn_modified_datetime = models.DateTimeField(blank=True, null=True)
    wn_created_datetime = models.DateTimeField(blank=True, null=True)
    duplicate = models.BooleanField(default=False)
    images = models.JSONField(default=list)

    reserved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="reserved_observations", on_delete=models.SET_NULL, null=True
    )
    reserved_datetime = models.DateTimeField(blank=True, null=True)

    eradication_datetime = models.DateTimeField(blank=True, null=True)
    eradicator_name = models.CharField(max_length=255, blank=True, null=True)
    eradication_duration = models.TimeField(blank=True, null=True)
    eradication_persons = models.IntegerField(blank=True, null=True)
    eradication_result = models.CharField(max_length=50, choices=EradicationResultEnum, blank=True, null=True)
    eradication_product = models.CharField(max_length=50, choices=EradicationProductEnum, blank=True, null=True)
    eradication_method = models.CharField(max_length=50, choices=EradicationMethodEnum, blank=True, null=True)
    eradication_aftercare = models.CharField(max_length=50, choices=EradicationAfterCareEnum, blank=True, null=True)
    eradication_problems = models.CharField(max_length=50, choices=EradicationProblemsEnum, blank=True, null=True)
    eradication_notes = models.TextField(blank=True, null=True)

    municipality = models.ForeignKey(
        Municipality,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="observations",
    )
    province = models.ForeignKey(
        Province,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="observations",
    )
    anb = models.BooleanField(default=False)
    public_domain = models.BooleanField(blank=True, null=True)

    def __str__(self) -> str:
        """Return the string representation of the model."""
        return f"Observation {self.id} - location: {self.location} - eradicated: {self.eradication_datetime}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Override the save method to automatically assign a municipality and ANB bool based on the observation's location.

        :param args: Variable length argument list.
        :param kwargs: Arbitrary keyword arguments.
        """
        # Only compute the municipality if the location is set and the municipality is not
        if self.location:
            # Ensure self.location is a Point instance
            if not isinstance(self.location, Point):
                self.location = Point(self.location)

            long = self.location.x
            lat = self.location.y

            self.anb = check_if_point_in_anb_area(long, lat)
            municipality = get_municipality_from_coordinates(long, lat)
            self.municipality = municipality
            self.province = municipality.province if municipality else None

        super().save(*args, **kwargs)
