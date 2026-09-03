from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory
from django.utils import translation

from integreat_cms.cms.views.utils.machine_translation_progress import (
    _get_failure_reason,
    _get_result_details,
    get_machine_translation_task_progress,
)

# --- _get_failure_reason ---


def test_get_failure_reason_translates_known_causes() -> None:
    with translation.override("en"):
        assert (
            _get_failure_reason("User not found")
            == "the triggering user could not be found"
        )
        assert (
            _get_failure_reason("Region not found")
            == "the requested region could not be found"
        )
        assert (
            _get_failure_reason("Content type not found")
            == "the requested content type is not supported"
        )


def test_get_failure_reason_passes_through_unknown_message() -> None:
    assert (
        _get_failure_reason("Something unexpected happened")
        == "Something unexpected happened"
    )


# --- _get_result_details ---


def test_result_details_composes_failure_message() -> None:
    result = MagicMock(
        state="FAILURE", info=ValueError("Something unexpected happened")
    )

    details = _get_result_details(result)

    assert "Something unexpected happened" in details["message"]
    assert "message" in details
    assert len(details) == 1


def test_result_details_composes_failure_message_for_known_cause() -> None:
    result = MagicMock(state="FAILURE", info=ValueError("User not found"))

    with translation.override("en"):
        details = _get_result_details(result)

    assert "the triggering user could not be found" in details["message"]
    assert "User not found" not in details["message"]


def test_result_details_passes_through_non_failure_info_unchanged() -> None:
    result = MagicMock(state="SUCCESS", info={"progress": 1.0, "pages": {}})

    assert _get_result_details(result) == {"progress": 1.0, "pages": {}}


# --- get_machine_translation_task_progress ---


def test_get_machine_translation_task_progress_denies_without_permission() -> None:
    request = RequestFactory().get("/")
    request.user = MagicMock()
    request.user.has_perm = MagicMock(return_value=False)
    request.region = MagicMock(id=1)

    with pytest.raises(PermissionDenied):
        get_machine_translation_task_progress(request, "augsburg", "page", "task-1")


def test_get_machine_translation_task_progress_returns_status_and_details() -> None:
    request = RequestFactory().get("/")
    request.user = MagicMock()
    request.user.has_perm = MagicMock(return_value=True)
    request.region = MagicMock(id=1)

    fake_result = MagicMock(state="SUCCESS", info={"progress": 1.0, "pages": {}})
    fake_result.kwargs = {"region_id": 1, "content_type": "page"}

    with patch(
        "integreat_cms.cms.views.utils.machine_translation_progress.AsyncResult",
        return_value=fake_result,
    ):
        response = get_machine_translation_task_progress(
            request, "augsburg", "page", "task-1"
        )

    assert response.status_code == 200
    assert json.loads(response.content) == {
        "status": "SUCCESS",
        "details": {"progress": 1.0, "pages": {}},
    }


def test_get_machine_translation_task_progress_cross_region_permission_denied() -> None:
    request = RequestFactory().get("/")
    request.user = MagicMock()
    request.user.has_perm = MagicMock(return_value=True)
    request.region = MagicMock(id=1)

    fake_result = MagicMock(state="SUCCESS", info={"progress": 1.0, "pages": {}})
    fake_result.kwargs = {"region_id": 2, "content_type": "page"}

    with (
        patch(
            "integreat_cms.cms.views.utils.machine_translation_progress.AsyncResult",
            return_value=fake_result,
        ),
        pytest.raises(PermissionDenied),
    ):
        get_machine_translation_task_progress(request, "augsburg", "page", "task-1")


def test_get_machine_translation_task_progress_cross_content_type_permission_denied() -> (
    None
):
    request = RequestFactory().get("/")
    request.user = MagicMock()
    request.user.has_perm = MagicMock(return_value=True)
    request.region = MagicMock(id=1)

    fake_result = MagicMock(state="SUCCESS", info={"progress": 1.0, "pages": {}})
    fake_result.kwargs = {"region_id": 1, "content_type": "event"}

    with (
        patch(
            "integreat_cms.cms.views.utils.machine_translation_progress.AsyncResult",
            return_value=fake_result,
        ),
        pytest.raises(PermissionDenied),
    ):
        get_machine_translation_task_progress(request, "augsburg", "page", "task-1")


def test_get_machine_translation_task_progress_does_not_raise_when_status_pending() -> (
    None
):
    request = RequestFactory().get("/")
    request.user = MagicMock()
    request.user.has_perm = MagicMock(return_value=True)
    request.region = MagicMock(id=1)

    fake_result = MagicMock(state="PENDING", info=None)
    fake_result.kwargs = {"region_id": 2, "content_type": "event"}

    with patch(
        "integreat_cms.cms.views.utils.machine_translation_progress.AsyncResult",
        return_value=fake_result,
    ):
        response = get_machine_translation_task_progress(
            request, "augsburg", "page", "task-1"
        )

    assert response.status_code == 200
    assert json.loads(response.content) == {
        "status": "PENDING",
        "details": None,
    }
