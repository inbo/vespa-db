"""Observation models for the observations app."""

import logging
from typing import Any

from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.db import models
from django.utils.translation import gettext_lazy as _
from datetime import datetime
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

    ACTIVE_EMBRYONAL_NEST = "actief_embryonaal_nest", _("Actief embryonaal nest")
    ACTIVE_PRIMARY_NEST = "actief_primair_nest", _("Actief primair nest")
    ACTIVE_SECONDARY_NEST = "actief_secundair_nest", _("Actief secundair nest")
    INACTIVE_EMPTY_NEST = "inactief_leeg_nest", _("Inactief/leeg nest")


class EradicationResultEnum(models.TextChoices):
    """Enum for the result of the eradication."""

    SUCCESSFUL = "successful", _("Succesvol behandeld")
    UNSUCCESSFUL = "unsuccessful", _("Niet succesvol behandeld")
    UNTREATED = "untreated", _("Niet behandeld want andere soort")
    UNTREATABLE = "untreatable", _("Onbehandelbaar (bv. te hoog, inactief)")
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
    LOCKABLE_JAR_BOX = "doos", _("doos")
    LIQUID_SPRAYER = "vloeistofverstuiver", _("Vloeistofverstuiver")
    POWDER_SPRAYER = "poederverstuiver", _("Poederverstuiver")
    VACUUM_CLEANER = "stofzuiger", _("Stofzuiger")


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
        "steken",
        _("Steken"),
    )
    NEST_FALLING = (
        "nest_gevallen",
        _("Nest gevallen"),
    )
    DIZZINESS = (
        "duizeligheid",
        _("Duizeligheid"),
    )
    POISON_PROJECTION = (
        "gif_spuiten",
        _("Gif Spuiten"),
    )


class EradicationProductEnum(models.TextChoices):
    """Enum for the product used for the eradication."""

    PERMAS_D = "permas_d", _("Permas-D")
    LIQUID_NITROGEN = "vloeibare_stikstof", _("Vloeibare stikstof")
    FICAM_D = "ficam_d", _("Ficam D")
    TOPSCORE_PAL = "topscore_pal", _("Topscore PAL")
    DIATOMACEOUS_EARTH = "diatomeeenaarde", _("Diatomeeënaarde")
    ETHER_ACETONE_ETHYL_ACETATE = "ether_aceton_ethyl_acetaat", _("Ether, aceton of ethylacetaat")
    VESPA = "vespa", _("Vespa")
    OTHER = "andere", _("Andere")


class Province(models.Model):
    """Model voor de Belgische gemeenten met uitgebreide gegevens."""

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, help_text="Name of the province")
    nis_code = models.CharField(max_length=255, help_text="NIS code of the province")
    polygon = gis_models.MultiPolygonField(srid=31370, help_text="Geographical polygon of the province")

    oidn = models.BigIntegerField(blank=True, null=True, help_text="OIDN of the province")
    uidn = models.BigIntegerField(blank=True, null=True, help_text="UIDN of the province")
    terrid = models.BigIntegerField(blank=True, null=True, help_text="TERRID of the province")
    length = models.FloatField(blank=True, null=True, help_text="Length of the province boundary")
    surface = models.FloatField(blank=True, null=True, help_text="Surface area of the province")

    class Meta:
        """Meta class for the Province model."""

        unique_together = ("name",)
        ordering = ["name"]

    def __str__(self) -> str:
        """Return the string representation of the model."""
        return str(self.name)


class Municipality(models.Model):
    """Model voor de Belgische gemeenten met uitgebreide gegevens."""

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, help_text="Name of the municipality")
    nis_code = models.CharField(max_length=255, help_text="NIS code of the municipality")
    polygon = gis_models.MultiPolygonField(srid=31370, help_text="Geographical polygon of the municipality")

    oidn = models.BigIntegerField(blank=True, null=True, help_text="OIDN of the municipality")
    uidn = models.BigIntegerField(blank=True, null=True, help_text="UIDN of the municipality")
    terrid = models.BigIntegerField(blank=True, null=True, help_text="TERRID of the municipality")
    datpublbs = models.DateField(blank=True, null=True, help_text="Publication date of the municipality data")
    numac = models.CharField(max_length=10, blank=True, null=True, help_text="NUMAC of the municipality")
    length = models.FloatField(blank=True, null=True, help_text="Length of the municipality boundary")
    surface = models.FloatField(blank=True, null=True, help_text="Surface area of the municipality")
    province = models.ForeignKey(
        Province,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="municipalities",
        help_text="Province to which the municipality belongs",
    )

    class Meta:
        """Meta class for the Municipality model."""

        verbose_name_plural = "Municipalities"
        unique_together = ("name",)
        ordering = ["name"]

    def __str__(self) -> str:
        """Return the string representation of the model."""
        return str(self.name)


class ANB(models.Model):
    """Model for the Agentschap voor Natuur en Bos (ANB) domain with detailed data."""

    id = models.AutoField(primary_key=True)
    domain = models.CharField(max_length=255, help_text="Domain of the ANB")
    province = models.CharField(max_length=255, help_text="Province of the ANB")
    regio = models.CharField(max_length=255, null=True, help_text="Region of the ANB")
    liberties = models.CharField(max_length=255, null=True, help_text="Liberties of the ANB")
    administrator = models.CharField(max_length=255, null=True, help_text="Administrator of the ANB")
    contact = models.EmailField(max_length=255, null=True, help_text="Contact email of the ANB")
    polygon = gis_models.MultiPolygonField(srid=31370, help_text="Geographical polygon of the ANB")

    def __str__(self) -> str:
        """Return the string representation of the model."""
        return str(self.domain)


class Observation(models.Model):
    """Model for the observation of a Vespa velutina nest."""

    id = models.AutoField(primary_key=True)
    wn_id = models.IntegerField(unique=True, blank=True, null=True, help_text="Unique ID for the observation")
    created_datetime = models.DateTimeField(help_text="Datetime when the observation was created") 
    modified_datetime = models.DateTimeField(auto_now=True, help_text="Datetime when the observation was last modified")
    location = gis_models.PointField(help_text="Geographical location of the observation")
    source = models.CharField(max_length=255, blank=True, null=True, help_text="Source of the observation")
    source_id = models.IntegerField(blank=True, null=True, help_text="Original identifier when importing data")

    notes = models.TextField(blank=True, null=True, help_text="Notes about the observation")
    wn_admin_notes = models.TextField(blank=True, null=True, help_text="Admin notes about the observation")
    wn_validation_status = models.CharField(
        max_length=50,
        choices=ValidationStatusEnum.choices,
        blank=True,
        null=True,
        help_text="Validation status of the observation",
    )

    nest_height = models.CharField(
        max_length=50, choices=NestHeightEnum.choices, blank=True, null=True, help_text="Height of the nest"
    )
    nest_size = models.CharField(
        max_length=50, choices=NestSizeEnum.choices, blank=True, null=True, help_text="Size of the nest"
    )
    nest_location = models.CharField(
        max_length=50, choices=NestLocationEnum.choices, blank=True, null=True, help_text="Location of the nest"
    )
    nest_type = models.CharField(
        max_length=50, choices=NestTypeEnum.choices, blank=True, null=True, help_text="Type of the nest"
    )

    observer_phone_number = models.CharField(
        max_length=200, blank=True, null=True, help_text="Phone number of the observer"
    )
    observer_email = models.EmailField(blank=True, null=True, help_text="Email of the observer")
    observer_received_email = models.BooleanField(default=False, help_text="Flag indicating if observer received email")
    observer_name = models.CharField(max_length=255, blank=True, null=True, help_text="Name of the observer")
    observation_datetime = models.DateTimeField(null=True, blank=True, help_text="Datetime when the observation was made")

    wn_cluster_id = models.IntegerField(blank=True, null=True, help_text="Cluster ID of the observation")
    admin_notes = models.TextField(blank=True, null=True, help_text="Admin notes for the observation")

    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="modified_observations",
        on_delete=models.SET_NULL,
        null=True,
        help_text="User who last modified the observation",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="created_observations",
        on_delete=models.SET_NULL,
        null=True,
        help_text="User who created the observation",
    )
    wn_modified_datetime = models.DateTimeField(
        blank=True, null=True, help_text="Datetime when the observation was modified in the source system"
    )
    wn_created_datetime = models.DateTimeField(
        blank=True, null=True, help_text="Datetime when the observation was created in the source system"
    )
    # TODO: visible True in response & export. Frontend -> visible weg
    visible = models.BooleanField(null=True, default=True, help_text="Flag indicating if the observation is visible")
    images = models.JSONField(
        default=list, blank=True, null=True, help_text="List of images associated with the observation"
    )

    reserved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="reserved_observations",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who reserved the observation",
    )
    reserved_datetime = models.DateTimeField(
        blank=True, null=True, help_text="Datetime when the observation was reserved"
    )

    eradication_date = models.DateField(blank=True, null=True, help_text="Date when the nest was eradicated")
    eradicator_name = models.CharField(
        max_length=255, blank=True, null=True, help_text="Name of the person who eradicated the nest"
    )
    eradication_duration = models.PositiveIntegerField(
        blank=True, null=True, help_text="Duration of the eradication in minutes"
    )
    eradication_persons = models.IntegerField(
        blank=True, null=True, help_text="Number of persons involved in the eradication"
    )
    eradication_result = models.CharField(
        max_length=50,
        choices=EradicationResultEnum.choices,
        blank=True,
        null=True,
        help_text="Result of the eradication",
    )
    eradication_product = models.CharField(
        max_length=50,
        choices=EradicationProductEnum.choices,
        blank=True,
        null=True,
        help_text="Product used for the eradication",
    )
    eradication_method = models.CharField(
        max_length=50,
        choices=EradicationMethodEnum.choices,
        blank=True,
        null=True,
        help_text="Method used for the eradication",
    )
    eradication_aftercare = models.CharField(
        max_length=50,
        choices=EradicationAfterCareEnum.choices,
        blank=True,
        null=True,
        help_text="Aftercare result of the eradication",
    )
    eradication_problems = models.CharField(
        max_length=50,
        choices=EradicationProblemsEnum.choices,
        blank=True,
        null=True,
        help_text="Problems encountered during the eradication",
    )
    eradication_notes = models.TextField(blank=True, null=True, help_text="Notes about the eradication")
    
    queen_present = models.BooleanField(
        null=True,
        blank=True,
        help_text="Shows if the queen was present during the eradication",
    )
    moth_present = models.BooleanField(
        null=True,
        blank=True,
        help_text="Shows if moths were present during the eradication",
    )

    municipality = models.ForeignKey(
        Municipality,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="observations",
        help_text="Municipality where the observation was made",
    )
    province = models.ForeignKey(
        Province,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="observations",
        help_text="Province where the observation was made",
    )
    anb = models.BooleanField(default=False, help_text="Flag indicating if the observation is in ANB area")
    public_domain = models.BooleanField(
        blank=True, null=True, help_text="Flag indicating if the observation is in the public domain"
    )
    duplicate_nest = models.BooleanField(
        null=True,
        blank=True,
        help_text="Shows if the nest is a duplicate",
    )
    other_species_nest = models.BooleanField(
        null=True,
        blank=True,
        help_text="Shows if the nest belongs to another species",
    )


    def __str__(self) -> str:
        """Return the string representation of the model."""
        return f"Observation {self.id} - location: {self.location} - eradicated: {self.eradication_date}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Override the save method to automatically assign a municipality and ANB bool based on the observation's location.

        :param args: Variable length argument list.
        :param kwargs: Arbitrary keyword arguments.
        """
        logger.info(f"Saving observation with created_datetime={self.created_datetime}, pk={self.pk}")
        if self.location:
            if not isinstance(self.location, Point):
                self.location = Point(self.location)
            long, lat = self.location.x, self.location.y
            self.anb = check_if_point_in_anb_area(long, lat)
            if not self.municipality:
                municipality = get_municipality_from_coordinates(long, lat)
                self.municipality = municipality
                if municipality and not self.province:
                    self.province = municipality.province
        if self.modified_datetime is None:
            self.modified_datetime = datetime.now()
        if self.created_datetime is None and not self.pk:
            self.created_datetime = datetime.now()
            logger.info(f"Setting created_datetime to now: {self.created_datetime}")
        super().save(*args, **kwargs)
        logger.info(f"Saved observation with created_datetime={self.created_datetime}")
        
    class Meta:
        ordering = ['id']
        indexes = [
            models.Index(fields=['visible', 'observation_datetime']),
            gis_models.Index(fields=['location'], name='location_idx'),
            models.Index(fields=['municipality', 'visible']),
        ]

class Export(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    )

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who initiated the export",
    )
    file_path = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    progress = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    task_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Export {self.id} - {self.status}"

class Import(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    )

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who initiated the import",
    )
    file_path = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", help_text="Status of the import")
    progress = models.IntegerField(default=0, help_text="Progress percentage of the import")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Datetime when the import was created")
    completed_at = models.DateTimeField(blank=True, null=True, help_text="Datetime when the import was completed")
    error_message = models.TextField(blank=True, null=True, help_text="Error message if the import failed")
    task_id = models.CharField(max_length=255, blank=True, null=True, help_text="Celery task ID for the import")
    created_ids = models.JSONField(default=list, help_text="IDs of created observations")
    updated_ids = models.JSONField(default=list, help_text="IDs of updated observations")

    def __str__(self):
        return f"Import {self.id} - {self.status}"
