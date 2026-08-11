from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory
from django.test.client import Client
from django.urls import reverse

from integreat_cms.cms.models import Region
from integreat_cms.cms.views.utils.machine_translation_report import (
    _get_report_message,
    _get_report_outcome,
    get_machine_translation_report,
)
from integreat_cms.core.utils.machine_translation_celery_task import _queue_mt_report

if TYPE_CHECKING:
    from typing import Any

REGION_SLUG = "augsburg"


# --- _get_report_outcome ---


def test_report_outcome_full_success_when_nothing_failed() -> None:
    results = {"en": {"1": {"succeeded": "ok", "failed": {}}}}
    assert _get_report_outcome(results) == "FULL_SUCCESS"


def test_report_outcome_full_success_for_empty_results() -> None:
    assert _get_report_outcome({}) == "FULL_SUCCESS"


def test_report_outcome_partial_success_when_one_object_failed() -> None:
    results: dict[str, dict[str, dict[str, Any]]] = {
        "en": {
            "1": {"succeeded": "ok", "failed": {}},
            "2": {"exception": "provider exploded"},
        },
        "fa": {"1": {"succeeded": "ok", "failed": {}}},
    }
    assert _get_report_outcome(results) == "PARTIAL_SUCCESS"


def test_report_outcome_partial_success_for_failure_reported_via_failed_dict() -> None:
    """
    Regression test: `_get_language_report()`'s shape reports a failure via a
    populated "failed" bucket, not a top-level "exception" key - this
    happens whenever the API client catches its own provider exception
    internally (e.g. `mark_unsuccessful()`) and returns normally rather than
    raising. `_get_report_outcome` used to only check for "exception",
    so a batch that failed entirely this way (e.g. every object hit a
    DeepL API error) was misreported as "FULL_SUCCESS".
    """
    results = {
        "en": {
            "1": {
                "succeeded": "",
                "failed": {
                    "too-long": "",
                    "exceeds-limit": "",
                    "insufficient-hix": "",
                    "no-source-translation": "",
                    "no-changes-made": "",
                    "no-reason": "Page 'Foo' could not be translated automatically into 'en'",
                },
            },
        },
    }
    assert _get_report_outcome(results) == "PARTIAL_SUCCESS"


# --- _get_report_message ---


def test_report_message_differs_by_outcome() -> None:
    assert _get_report_message("FULL_SUCCESS") != _get_report_message("PARTIAL_SUCCESS")


def test_report_message_evaluates_translation_per_call_not_at_import() -> None:
    """
    Regression test: an early draft computed these messages via `gettext()`
    in a module-level dict, evaluated exactly once - at import time, under
    whatever language happened to be active then, not the requesting user's.
    Verify `_(...)` (the module's `gettext` alias) is actually invoked fresh
    on every call, rather than the result being read from something
    precomputed once and reused forever after.
    """
    with patch(
        "integreat_cms.cms.views.utils.machine_translation_report._",
        side_effect=lambda text: text,
    ) as mock_gettext:
        _get_report_message("FULL_SUCCESS")
        _get_report_message("FULL_SUCCESS")

    assert mock_gettext.call_count == 2


# --- get_machine_translation_report (view) ---


def test_get_machine_translation_report_denies_without_permission() -> None:
    request = RequestFactory().get("/")
    request.user = MagicMock()
    request.user.has_perm = MagicMock(return_value=False)

    with pytest.raises(PermissionDenied):
        get_machine_translation_report(request, REGION_SLUG, "en", "page")


@pytest.mark.django_db
def test_get_machine_translation_report_empty_when_nothing_queued(
    load_test_data: None,
) -> None:
    client = Client()
    client.force_login(get_user_model().objects.get(username="root"))
    url = reverse(
        "machine_translation_report",
        kwargs={
            "region_slug": REGION_SLUG,
            "language_slug": "en",
            "model_type": "page",
        },
    )

    response = client.get(url)

    assert response.status_code == 200
    assert response.json() == {"reports": []}


@pytest.mark.django_db
def test_get_machine_translation_report_is_destructive_read(
    load_test_data: None,
) -> None:
    user = get_user_model().objects.get(username="root")
    region = Region.objects.get(slug=REGION_SLUG)
    _queue_mt_report(
        user.id,
        region.id,
        "page",
        ["en"],
        {"en": {"1": {"succeeded": "ok", "failed": {}}}},
    )

    client = Client()
    client.force_login(user)
    url = reverse(
        "machine_translation_report",
        kwargs={
            "region_slug": REGION_SLUG,
            "language_slug": "en",
            "model_type": "page",
        },
    )

    first_response = client.get(url)
    second_response = client.get(url)

    assert first_response.status_code == 200
    first_data = first_response.json()
    assert len(first_data["reports"]) == 1
    report = first_data["reports"][0]
    assert report["language_slugs"] == ["en"]
    assert report["outcome"] == "FULL_SUCCESS"
    assert report["message"] == _get_report_message("FULL_SUCCESS")

    assert second_response.status_code == 200
    assert second_response.json() == {"reports": []}
