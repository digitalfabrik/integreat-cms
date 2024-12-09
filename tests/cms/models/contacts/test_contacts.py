from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest_django.fixtures import SettingsWrapper


import pytest
from django.utils import translation

from integreat_cms.cms.models import Contact


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
        == "Draft location with point of contact for: Integrationsbeauftragte"
    )

    contact_4 = Contact.objects.filter(id=4).first()
    assert (
        str(contact_4)
        == "Draft location with email: generalcontactinformation@example.com"
    )
