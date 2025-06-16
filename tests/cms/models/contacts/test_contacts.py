from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest_django.fixtures import SettingsWrapper


import pytest

from integreat_cms.cms.models import Contact


@pytest.mark.django_db
def test_contact_string(
    test_data_db_snapshot: None,
    db_snapshot: None,
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
    test_data_db_snapshot: None,
    db_snapshot: None,
) -> None:
    assert Contact.objects.all().count() == 5

    contact = Contact.objects.get(id=1)
    contact.copy()

    assert Contact.objects.all().count() == 6


@pytest.mark.django_db
def test_deleting_contact_works(
    test_data_db_snapshot: None,
    db_snapshot: None,
) -> None:
    assert Contact.objects.all().count() == 5

    contact = Contact.objects.get(id=1)
    contact.delete()

    assert Contact.objects.all().count() == 4


@pytest.mark.django_db
def test_archiving_contact_works(
    test_data_db_snapshot: None,
    db_snapshot: None,
) -> None:
    assert Contact.objects.all().count() == 5

    contact = Contact.objects.get(id=1)
    assert contact.archived is False
    contact.archive()

    assert Contact.objects.all().count() == 5
    assert contact.archived is True


@pytest.mark.django_db
def test_restoring_contact_works(
    test_data_db_snapshot: None,
    db_snapshot: None,
) -> None:
    assert Contact.objects.all().count() == 5

    contact = Contact.objects.get(id=2)
    assert contact.archived is True
    contact.restore()

    assert Contact.objects.all().count() == 5
    assert contact.archived is False
