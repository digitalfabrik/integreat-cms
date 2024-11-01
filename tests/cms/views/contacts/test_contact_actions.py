import pytest
from django.test.client import Client

from integreat_cms.cms.models.contact.contact import Contact


@pytest.mark.django_db
def test_copying_contact_works(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    assert Contact.objects.all().count() == 4

    contact = Contact.objects.get(id=1)
    contact.copy()

    assert Contact.objects.all().count() == 5


@pytest.mark.django_db
def test_deleting_contact_works(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    assert Contact.objects.all().count() == 4

    contact = Contact.objects.get(id=1)
    contact.delete()

    assert Contact.objects.all().count() == 3


@pytest.mark.django_db
def test_archiving_contact_works(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    assert Contact.objects.all().count() == 4

    contact = Contact.objects.get(id=1)
    assert contact.archived is False
    contact.archive()

    assert Contact.objects.all().count() == 4
    assert contact.archived is True


@pytest.mark.django_db
def test_restoring_contact_works(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    assert Contact.objects.all().count() == 4

    contact = Contact.objects.get(id=2)
    assert contact.archived is True
    contact.restore()

    assert Contact.objects.all().count() == 4
    assert contact.archived is False
