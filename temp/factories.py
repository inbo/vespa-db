"""factories."""
from vespadb.observations.models import Observation, Municipality, NestHeightEnum, NestSizeEnum, NestLocationEnum, NestTypeEnum, EradicationResultEnum, EradicationProductEnum
import factory
from django.contrib.gis.geos import MultiPolygon, Polygon
from vespadb.observations.models import Municipality
import factory.fuzzy
from django.contrib.gis.geos import Point
from django.utils import timezone
from helpers import get_random_municipality, get_point_from_municipality
from typing import Tuple, Optional

class MunicipalityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Municipality

    @factory.lazy_attribute
    def municipality_data(self) -> Tuple[Optional[str], Optional[str], Optional[MultiPolygon]]:
        # This fetches a single municipality's data and uses it across all fields
        name, nis_code, polygon = get_random_municipality()
        return (name, nis_code, polygon)

    name = factory.LazyAttribute(lambda obj: obj.municipality_data[0])
    nis_code = factory.LazyAttribute(lambda obj: obj.municipality_data[1])
    polygon = factory.LazyAttribute(lambda obj: obj.municipality_data[2])
    
class ObservationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Observation

    wn_id = factory.Sequence(lambda n: n)
    created_datetime = factory.LazyFunction(timezone.now)
    modified_datetime = factory.LazyFunction(timezone.now)
    location = factory.LazyAttribute(lambda obj: get_point_from_municipality(get_random_municipality()[2], inside=True))
    source = factory.Faker('word')
    species = factory.fuzzy.FuzzyChoice([x for x in range(100)])
    nest_height = factory.fuzzy.FuzzyChoice(NestHeightEnum.values)
    nest_size = factory.fuzzy.FuzzyChoice(NestSizeEnum.values)
    nest_location = factory.fuzzy.FuzzyChoice(NestLocationEnum.values)
    nest_type = factory.fuzzy.FuzzyChoice(NestTypeEnum.values)
    observer_phone_number = factory.Faker('phone_number')
    observer_email = factory.Faker('email')
    observer_name = factory.Faker('name')
    observer_allows_contact = factory.Faker('boolean')
    observation_datetime = factory.LazyFunction(timezone.now)
    eradication_datetime = factory.LazyFunction(timezone.now)
    eradicator_name = factory.Faker('name')
    eradication_result = factory.fuzzy.FuzzyChoice(EradicationResultEnum.values)
    eradication_product = factory.fuzzy.FuzzyChoice(EradicationProductEnum.values)
    eradication_notes = factory.Faker('text')
    duplicate = factory.Faker('boolean')
    images = factory.LazyFunction(lambda: [])
