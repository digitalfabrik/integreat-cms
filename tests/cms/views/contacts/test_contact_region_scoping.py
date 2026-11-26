"""
Regression tests ensuring that a contact can only be assigned to a place of the
current region.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.urls import reverse

from integreat_cms.cms.models import Contact

if TYPE_CHECKING:
    from django.test.client import Client

from tests.constants import ANONYMOUS

OWN_REGION_SLUG = "augsburg"
# Place 7 belongs to "berlin"
FOREIGN_PLACE_ID = 7
# Contact 1 belongs to place 6 in "augsburg"
OWN_CONTACT_ID = 1

CONTACT_DATA = {
    "place": FOREIGN_PLACE_ID,
    "area_of_responsibility": "Cross region",
    "name": "Cross region contact",
    "email": "mail@mail.integreat",
    "phone_number": "0123456789",
    "website": "https://integreat-app.de/",
    "use_place_opening_hours": True,
    "opening_hours": "null",
}


@pytest.mark.django_db
def test_create_contact_with_foreign_place_is_rejected(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    client, role = login_role_user
    contact_count_before = Contact.objects.filter(place_id=FOREIGN_PLACE_ID).count()

    url = reverse("new_contact", kwargs={"region_slug": OWN_REGION_SLUG})
    response = client.post(url, data=CONTACT_DATA)

    if role == ANONYMOUS:
        assert response.status_code == 302
    else:
        assert response.status_code in (200, 403)

    assert (
        Contact.objects.filter(place_id=FOREIGN_PLACE_ID).count()
        == contact_count_before
    )
    assert not Contact.objects.filter(name="Cross region contact").exists()


@pytest.mark.django_db
def test_move_contact_to_foreign_place_is_rejected(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    client, role = login_role_user
    place_before = Contact.objects.get(id=OWN_CONTACT_ID).place_id

    url = reverse(
        "edit_contact",
        kwargs={"region_slug": OWN_REGION_SLUG, "contact_id": OWN_CONTACT_ID},
    )
    response = client.post(url, data=CONTACT_DATA)

    if role == ANONYMOUS:
        assert response.status_code == 302
    else:
        assert response.status_code in (200, 403)

    assert Contact.objects.get(id=OWN_CONTACT_ID).place_id == place_before
