from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.db import models
from django.utils.translation import gettext_lazy as _


class SourceEnum(models.TextChoices):
    """Enum for the source of the observation report."""

    OBSERVATIONS_API = "OA", _("Observations API")
    USER = "UR", _("User")
    IMPORT = "IM", _("Import")


class ObservationStatusEnum(models.TextChoices):
    """Enum for the status of the observation."""

    UNTREATED = "UT", _("Untreated")
    TREATED = "TR", _("Treated")


class ObservationHeightEnum(models.TextChoices):
    """Enum for the height of the observation."""

    BELOW_4_METERS = "BL4", _("Below 4 meters")
    ABOVE_4_METERS = "AB4", _("Above 4 meters")


class ObservationLocationEnum(models.TextChoices):
    """Enum for the location of the observation."""

    OUTDOOR_UNCOVERED_ON_BUILDING = "OUB", _("Outdoor, uncovered on building")
    OUTDOOR_UNCOVERED_IN_TREE = "OUT", _("Outdoor, uncovered in tree or bush")
    OUTDOOR_COVERED_BY_STRUCTURE = "OCS", _("Outdoor, covered by structure")
    OUTDOOR_NATURALLY_COVERED = "ONC", _("Outdoor, naturally covered")
    INDOOR_IN_BUILDING = "IIB", _("Indoor, in building or structure")
    UNKNOWN = "UNK", _("Unknown")


class ObservationTypeEnum(models.TextChoices):
    """Enum for the type of the observation."""

    ACTIVE_EMBRYONIC = "AEM", _("Active embryonic observation")
    ACTIVE_PRIMARY = "APR", _("Active primary observation")
    ACTIVE_SECONDARY = "ASE", _("Active secondary observation")
    INACTIVE_EMPTY = "IEM", _("Inactive/empty observation")
    POTENTIAL = "POT", _("Potential observation (more info needed)")
    OTHER_SPECIES = "OSP", _("Observation of another species")
    NO_OBSERVATION = "NON", _("No observation (object, insect)")


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
    """Enum for the problems with the observation."""

    NONE = "NON", _("None")
    STINGS = "STI", _("Stings")
    OBSERVATION_FALLEN = "NFAL", _("Observation fallen")
    DIZZINESS_NAUSEA = "DIZ", _("Dizziness/nausea")
    CHEMICAL_PROJECTION = "CHE", _("Chemical projection")
    UNKNOWN = "UNK", _("Unknown")


class CareEnum(models.TextChoices):
    """Enum for the care of the observation."""

    OBSERVATION_FULLY_REMOVED = "NFR", _("Observation fully removed")
    OBSERVATION_PARTIALLY_REMOVED = "NPR", _("Observation partially removed")
    OBSERVATION_LEFT_HANGING = "NLH", _("Observation left hanging")
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
    """Enum for the province of the observation."""

    WEST_FLANDERS = "WF", _("West Flanders")
    EAST_FLANDERS = "EF", _("East Flanders")
    ANTWERP = "ANT", _("Antwerp")
    FLEMISH_BRABANT = "FB", _("Flemish Brabant")
    LIMBURG = "LIM", _("Limburg")
    NON_FLEMISH = "NF", _("Non-Flemish")
    UNKNOWN = "UNK", _("Unknown")
