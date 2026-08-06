from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest_django.fixtures import SettingsWrapper


import pytest

from integreat_cms.cms.constants import poicategory
from integreat_cms.cms.models import (
    Contact,
    Language,
    POI,
    POICategory,
    POITranslation,
    Region,
)


@pytest.mark.django_db
def test_contact_string(
    load_test_data: None,
    settings: SettingsWrapper,
) -> None:
    """
    Test whether __str__ of contact model works as expected
    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    """
    settings.LANGUAGE_CODE = "en"

    contact_1 = Contact.objects.filter(id=1).first()
    assert (
        str(contact_1)
        == "Draft location with area of responsibility: Integrationsberatung"
    )

    contact_4 = Contact.objects.filter(id=4).first()
    assert (
        str(contact_4)
        == "Draft location with email: generalcontactinformation@example.com"
    )


@pytest.mark.django_db
def test_copying_contact_works(
    load_test_data: None,
) -> None:
    assert Contact.objects.all().count() == 6

    contact = Contact.objects.get(id=1)
    contact.copy()

    assert Contact.objects.all().count() == 7


@pytest.mark.django_db
def test_deleting_contact_works(
    load_test_data: None,
) -> None:
    assert Contact.objects.all().count() == 6

    contact = Contact.objects.get(id=1)
    contact.delete()

    assert Contact.objects.all().count() == 5


@pytest.mark.django_db
def test_archiving_contact_works(
    load_test_data: None,
) -> None:
    assert Contact.objects.all().count() == 6

    contact = Contact.objects.get(id=1)
    assert contact.archived is False
    contact.archive()

    assert Contact.objects.all().count() == 6
    assert contact.archived is True


@pytest.mark.django_db
def test_restoring_contact_works(
    load_test_data: None,
) -> None:
    assert Contact.objects.all().count() == 6

    contact = Contact.objects.get(id=2)
    assert contact.archived is True
    contact.restore()

    assert Contact.objects.all().count() == 6
    assert contact.archived is False


@pytest.mark.django_db
def test_contact_restore_with_referenced_poi() -> None:
    """
    Tests restoring a contact restores its location together.
    """
    region = Region.objects.create(name="new-region")
    language = Language.objects.create(slug="da", primary_country_code="de")

    poi_category = POICategory.objects.create(
        icon=poicategory.OTHER,
        color=poicategory.DARK_BLUE,
    )
    poi = POI.objects.create(
        region=region,
        address="Adress 42",
        postcode="00000",
        city="Augsburg",
        country="Deutschland",
        latitude="48.3780446",
        longitude="10.8879783",
        category=poi_category,
        archived=True,
    )
    POITranslation.objects.create(poi=poi, language=language, slug="new-poi-slug")

    contact = Contact.objects.create(
        email="",
        phone_number="+49 123456789",
        website="",
        area_of_responsibility="Title",
        name="Contact",
        location=poi,
        archived=True,
    )

    assert contact.archived
    assert poi.archived
    assert contact.location.id == poi.id

    contact.restore()

    assert not contact.archived
    assert not poi.archived
