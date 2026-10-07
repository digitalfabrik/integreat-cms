from __future__ import annotations

import json
import re

import pytest
from django.contrib.auth import get_user_model
from django.test.client import Client
from django.urls import reverse

from tests.constants import ANONYMOUS, PRIV_STAFF_ROLES


@pytest.mark.django_db
@pytest.mark.parametrize("model_type", ["page", "event", "place"])
@pytest.mark.parametrize(
    ("title", "expected_slug"),
    [
        ("A new title", "a-new-title"),
        # A title without any sluggable characters falls back to the model type
        ("!!!", None),
    ],
)
def test_slugify_ajax_for_new_object(
    load_test_data: None,
    login_role_user: tuple[Client, str],
    model_type: str,
    title: str,
    expected_slug: str | None,
) -> None:
    """
    New objects have no ``model_id`` yet. Generating a slug for them must not fail (see #4225).
    """
    client, role = login_role_user

    response = client.post(
        reverse(
            "slugify_ajax",
            kwargs={
                "region_slug": "augsburg",
                "language_slug": "de",
                "model_type": model_type,
            },
        ),
        data=json.dumps({"title": title}),
        content_type="application/json",
    )

    if role == ANONYMOUS:
        assert response.status_code == 302
        return
    assert response.status_code in (200, 403)
    if role in PRIV_STAFF_ROLES:
        assert response.status_code == 200
        # The slug may get a counter suffix if it already exists
        assert re.fullmatch(
            rf"{expected_slug or model_type}(-\d+)?", response.json()["unique_slug"]
        )


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("page_id", "expected_status"),
    [
        # The observer is an explicit editor of page 6
        (6, 200),
        # ...but has no access to page 1
        (1, 403),
    ],
)
def test_slugify_ajax_for_new_translation_with_page_permission(
    load_test_data: None,
    page_id: int,
    expected_status: int,
) -> None:
    """
    Users with explicit page permissions can generate slugs for new translations of their pages.
    """
    client = Client()
    client.force_login(get_user_model().objects.get(username="observer"))

    response = client.post(
        reverse(
            "slugify_ajax",
            kwargs={
                "region_slug": "augsburg",
                "language_slug": "en",
                "model_type": "page",
            },
        ),
        data=json.dumps({"title": "A new title", "model_id": page_id}),
        content_type="application/json",
    )

    assert response.status_code == expected_status
