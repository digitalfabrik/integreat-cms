import pytest

from integreat_cms.cms.constants import poicategory
from integreat_cms.cms.models import Language, POI, POICategory, POITranslation, Region


@pytest.mark.django_db
def test_creating_poi_translations_to_automatically_create_unique_slugs() -> None:
    region = Region.objects.create(name="new-region")
    poi_category = POICategory.objects.create(
        icon=poicategory.OTHER,
        color=poicategory.DARK_BLUE,
    )
    poi1 = POI.objects.create(
        region=region,
        address="Adress 42",
        postcode="00000",
        city="Augsburg",
        country="Deutschland",
        latitude="48.3780446",
        longitude="10.8879783",
        category=poi_category,
    )
    poi2 = POI.objects.create(
        region=region,
        address="Adress 42",
        postcode="00000",
        city="Augsburg",
        country="Deutschland",
        latitude="48.3780446",
        longitude="10.8879783",
        category=poi_category,
    )
    language = Language.objects.create(
        slug="da", bcp47_tag="du_DU", primary_country_code="de"
    )
    poi_translation1 = POITranslation.objects.create(
        poi=poi1, language=language, slug="new-slug"
    )
    poi_translation2 = POITranslation.objects.create(
        poi=poi2, language=language, slug="new-slug"
    )
    assert poi_translation1.slug != poi_translation2.slug
