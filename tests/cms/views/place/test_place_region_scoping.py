"""
Regression tests ensuring that place views only resolve places of the current region
(a place of another region must not be accessible by combining a foreign place id
with the URL of the user's own region).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.urls import reverse

from integreat_cms.cms.models import Place

if TYPE_CHECKING:
    from django.test.client import Client

from tests.constants import ANONYMOUS

# Place 5 belongs to "nurnberg", the URLs below use "augsburg"
OWN_REGION_SLUG = "augsburg"
FOREIGN_PLACE_ID = 5


def _url(view_name: str) -> str:
    return reverse(
        view_name,
        kwargs={
            "region_slug": OWN_REGION_SLUG,
            "language_slug": "de",
            "place_id": FOREIGN_PLACE_ID,
        },
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "view_name", ["archive_place", "restore_place", "delete_place", "copy_place"]
)
def test_place_actions_are_region_scoped(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    view_name: str,
) -> None:
    client, role = login_role_user
    place = Place.objects.get(id=FOREIGN_PLACE_ID)
    assert place.region.slug != OWN_REGION_SLUG
    archived_before = place.archived
    place_count_before = Place.objects.count()

    response = client.post(_url(view_name))

    if role == ANONYMOUS:
        assert response.status_code == 302
    else:
        assert response.status_code in (403, 404)

    place = Place.objects.get(id=FOREIGN_PLACE_ID)
    assert place.archived == archived_before
    assert place.region.slug != OWN_REGION_SLUG
    assert Place.objects.count() == place_count_before


@pytest.mark.django_db
def test_place_view_is_region_scoped(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    client, role = login_role_user
    response = client.get(_url("view_place"))
    if role == ANONYMOUS:
        assert response.status_code == 302
    else:
        assert response.status_code in (403, 404)


@pytest.mark.django_db
def test_place_form_is_region_scoped(
    load_test_data: None,
    login_role_user: tuple[Client, str],
) -> None:
    client, role = login_role_user
    place = Place.objects.get(id=FOREIGN_PLACE_ID)
    region_before = place.region_id
    address_before = place.address

    url = _url("edit_place")

    response = client.get(url)
    if role == ANONYMOUS:
        assert response.status_code == 302
    else:
        assert response.status_code in (403, 404)

    response = client.post(
        url,
        data={
            "title": "Hijacked place",
            "address": "Evil street 1",
            "postcode": "86150",
            "city": "Augsburg",
            "country": "Deutschland",
            "status": "PUBLIC",
        },
    )
    if role == ANONYMOUS:
        assert response.status_code == 302
    else:
        assert response.status_code in (403, 404)

    place = Place.objects.get(id=FOREIGN_PLACE_ID)
    assert place.region_id == region_before
    assert place.address == address_before
