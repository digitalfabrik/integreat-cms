from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.test.client import Client

import re

import pytest
from django.apps import apps
from django.urls import reverse

from ..conftest import EDITOR, MANAGEMENT, PRIV_STAFF_ROLES


@pytest.mark.django_db
def test_mt_button_visibility(
    test_data_db_snapshot: None,
    db_snapshot: None,
    login_role_user: tuple[Client, str],
) -> None:
    """
    Check that MT button is invisible for users without publishing rights
    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    """
    apps.get_app_config("deepl_api").supported_source_languages = "de"
    apps.get_app_config("deepl_api").supported_target_languages = "en"

    client, role = login_role_user
    page = reverse(
        "edit_page",
        kwargs={"region_slug": "augsburg", "language_slug": "de", "page_id": 4},
    )
    data = {
        "title": "Neuer Titel",
        "content": "Neuer Inhalt",
        "mirrored_page_region": "",
    }

    response = client.post(page, data=data)
    pattern = r'<input[^>]*id="id_automatic_translation"[^>]*>'
    match = re.search(pattern, response.content.decode())
    if role in [*PRIV_STAFF_ROLES, EDITOR, MANAGEMENT]:
        assert match is not None, f"MT button should be visible for role {role}"
    else:
        assert match is None, f"MT button should not be visible for role {role}"
