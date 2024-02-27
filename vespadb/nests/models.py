"""Nest models for the nests app."""

from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.db import models
from django.utils.translation import gettext_lazy as _


class SourceEnum(models.TextChoices):
    """Enum for the source of the nest report."""

    OBSERVATIONS_API = "OA", _("Observations API")
    USER = "UR", _("User")
    IMPORT = "IM", _("Import")


class NestStatusEnum(models.TextChoices):
    """Enum for the status of the nest."""

    UNTREATED = "UT", _("Untreated")
    TREATED = "TR", _("Treated")


class NestHeightEnum(models.TextChoices):
    """Enum for the height of the nest."""

    BELOW_4_METERS = "BL4", _("Below 4 meters")
    ABOVE_4_METERS = "AB4", _("Above 4 meters")


class NestLocationEnum(models.TextChoices):
    """Enum for the location of the nest."""

    OUTDOOR_UNCOVERED_ON_BUILDING = "OUB", _("Outdoor, uncovered on building")
    OUTDOOR_UNCOVERED_IN_TREE = "OUT", _("Outdoor, uncovered in tree or bush")
    OUTDOOR_COVERED_BY_STRUCTURE = "OCS", _("Outdoor, covered by structure")
    OUTDOOR_NATURALLY_COVERED = "ONC", _("Outdoor, naturally covered")
    INDOOR_IN_BUILDING = "IIB", _("Indoor, in building or structure")
    UNKNOWN = "UNK", _("Unknown")


class NestTypeEnum(models.TextChoices):
    """Enum for the type of the nest."""

    ACTIVE_EMBRYONIC = "AEM", _("Active embryonic nest")
    ACTIVE_PRIMARY = "APR", _("Active primary nest")
    ACTIVE_SECONDARY = "ASE", _("Active secondary nest")
    INACTIVE_EMPTY = "IEM", _("Inactive/empty nest")
    POTENTIAL = "POT", _("Potential nest (more info needed)")
    OTHER_SPECIES = "OSP", _("Nest of another species")
    NO_NEST = "NON", _("No nest (object, insect)")


class YesNoUnknownEnum(models.TextChoices):
    """Enum for yes, no, and unknown."""

    YES = "YES", _("Yes")
    NO = "NO", _("No")
    UNKNOWN = "UNK", _("Unknown")


class ResultEnum(models.TextChoices):
    """Enum for the result of the treatment."""

    SUCCESSFULLY_TREATED = "SUC", _("Successfully treated")
    NOT_SUCCESSFULLY_TREATED = "NST", _("Not successfully treated")
    NOT_TREATED = "NTR", _("Not treated")
    UNKNOWN = "UNK", _("Unknown")


class ProblemEnum(models.TextChoices):
    """Enum for the problems with the nest."""

    NONE = "NON", _("None")
    STINGS = "STI", _("Stings")
    NEST_FALLEN = "NFAL", _("Nest fallen")
    DIZZINESS_NAUSEA = "DIZ", _("Dizziness/nausea")
    CHEMICAL_PROJECTION = "CHE", _("Chemical projection")
    UNKNOWN = "UNK", _("Unknown")


class CareEnum(models.TextChoices):
    """Enum for the care of the nest."""

    NEST_FULLY_REMOVED = "NFR", _("Nest fully removed")
    NEST_PARTIALLY_REMOVED = "NPR", _("Nest partially removed")
    NEST_LEFT_HANGING = "NLH", _("Nest left hanging")
    UNKNOWN = "UNK", _("Unknown")


class ProductEnum(models.TextChoices):
    """Enum for the product used for the treatment."""

    PERMAS_D = "PER", _("Permas-D")
    LIQUID_NITROGEN = "LN", _("Liquid nitrogen")
    VESPA_FICAM_D = "VF", _("Vespa Ficam D")
    TOPSCORE_PAL = "TP", _("Topscore PAL")
    ETHER_ACETONE_ETHYL_ACETATE = "EAE", _("Ether/aceton/ethyl acetate")
    DIATOMACEOUS_EARTH = "DE", _("Diatomaceous earth")
    OTHER = "OTH", _("Other")
    NONE = "NON", _("None")
    UNKNOWN = "UNK", _("Unknown")


class MethodEnum(models.TextChoices):
    """Enum for the method used for the treatment."""

    FREEZING = "FRZ", _("Freezing")
    TELESCOPIC_POLE = "TLP", _("Telescopic pole")
    SEALABLE_CONTAINER = "SC", _("Sealable container/box")
    LIQUID_SPRAYER = "LS", _("Liquid sprayer")
    POWDER_SPRAYER = "PS", _("Powder sprayer")
    NOT_TREATED = "NT", _("Not treated")
    OTHER = "OTH", _("Other")
    UNKNOWN = "UNK", _("Unknown")


class ProvinceEnum(models.TextChoices):
    """Enum for the province of the nest."""

    WEST_FLANDERS = "WF", _("West Flanders")
    EAST_FLANDERS = "EF", _("East Flanders")
    ANTWERP = "ANT", _("Antwerp")
    FLEMISH_BRABANT = "FB", _("Flemish Brabant")
    LIMBURG = "LIM", _("Limburg")
    NON_FLEMISH = "NF", _("Non-Flemish")
    UNKNOWN = "UNK", _("Unknown")


class Nest(models.Model):
    """Model for a Vespa velutina nest."""

    id = models.AutoField(primary_key=True)
    creation_datetime = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=2, choices=SourceEnum.choices, default=SourceEnum.OBSERVATIONS_API)
    status = models.CharField(max_length=2, choices=NestStatusEnum.choices, default=NestStatusEnum.UNTREATED)
    validated = models.CharField(max_length=3, choices=YesNoUnknownEnum.choices, default=YesNoUnknownEnum.UNKNOWN)
    deleted = models.BooleanField(default=True)
    last_modification_datetime = models.DateTimeField(auto_now=True)

    # Reporter details
    reporter_phone_number = models.CharField(max_length=20, blank=True, null=True)
    reporter_email = models.EmailField()
    reported_datetime = models.DateTimeField()

    # Extermination details
    exterminator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="nests_handled",
        null=True,
        blank=True,
    )
    extermination_datetime = models.DateTimeField(blank=True, null=True)

    # Nest details
    location = gis_models.PointField()
    address = models.CharField(max_length=255, blank=True, null=True)
    images = models.JSONField(default=list)
    nature_reserve = models.BooleanField()
    nest_height = models.CharField(max_length=3, choices=NestHeightEnum.choices, blank=True, null=True)
    nest_location = models.CharField(max_length=3, choices=NestLocationEnum.choices, blank=True, null=True)
    remarks = models.TextField(max_length=5000, blank=True, null=True)
    nest_type = models.CharField(max_length=3, choices=NestTypeEnum.choices, blank=True, null=True)
    feedback_provided = models.CharField(
        max_length=3, choices=YesNoUnknownEnum.choices, default=YesNoUnknownEnum.UNKNOWN
    )
    managed = models.CharField(max_length=3, choices=YesNoUnknownEnum.choices, default=YesNoUnknownEnum.UNKNOWN)
    duplicate = models.CharField(max_length=3, choices=YesNoUnknownEnum.choices, default=YesNoUnknownEnum.UNKNOWN)
    public_domain = models.CharField(max_length=3, choices=YesNoUnknownEnum.choices, default=YesNoUnknownEnum.UNKNOWN)
    result = models.CharField(max_length=3, choices=ResultEnum.choices, default=ResultEnum.UNKNOWN)
    problems = models.CharField(max_length=4, choices=ProblemEnum.choices, default=ProblemEnum.UNKNOWN)
    care = models.CharField(max_length=3, choices=CareEnum.choices, default=CareEnum.UNKNOWN)
    product = models.CharField(max_length=3, choices=ProductEnum.choices, default=ProductEnum.UNKNOWN)
    method = models.CharField(max_length=3, choices=MethodEnum.choices, default=MethodEnum.UNKNOWN)
    extermination_file_number = models.CharField(max_length=255, blank=True, null=True)
    extermination_photos = models.JSONField(default=list)  # List of extermination photo file names
    ANB_area = models.CharField(max_length=3, choices=YesNoUnknownEnum.choices, default=YesNoUnknownEnum.UNKNOWN)
    province = models.CharField(max_length=3, choices=ProvinceEnum.choices, default=ProvinceEnum.UNKNOWN)

    class Meta:
        """Meta class for the Nest model."""

        verbose_name = "Nest"
        verbose_name_plural = "Nests"

    def __str__(self) -> str:
        """Return the string representation of the nest."""
        return f"Nest {self.pk} - {self.status}"
