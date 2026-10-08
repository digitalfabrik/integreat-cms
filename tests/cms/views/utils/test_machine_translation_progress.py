from __future__ import annotations

import json
import logging
from unittest.mock import MagicMock, patch

import pytest
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory

from integreat_cms.cms.views.utils.machine_translation_progress import (
    _get_result_details,
    get_machine_translation_task_progress,
)

# --- _get_result_details ---


def test_result_details_logs_the_cause_for_debugging(
    caplog: pytest.LogCaptureFixture,
) -> None:
    result = MagicMock(state="FAILURE", info=ValueError("User not found"))
    result.id = "task-1"

    with caplog.at_level(logging.ERROR):
        _get_result_details(result)

    assert "task-1" in caplog.text
    assert "User not found" in caplog.text


def test_result_details_passes_through_non_failure_info_unchanged() -> None:
    result = MagicMock(state="SUCCESS", info={"progress": 1.0, "content_objects": {}})

    assert _get_result_details(result) == {"progress": 1.0, "content_objects": {}}


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

    fake_result = MagicMock(
        state="SUCCESS", info={"progress": 1.0, "content_objects": {}}
    )
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
        "details": {"progress": 1.0, "content_objects": {}},
    }


def test_get_machine_translation_task_progress_cross_region_permission_denied() -> None:
    request = RequestFactory().get("/")
    request.user = MagicMock()
    request.user.has_perm = MagicMock(return_value=True)
    request.region = MagicMock(id=1)

    fake_result = MagicMock(
        state="SUCCESS", info={"progress": 1.0, "content_objects": {}}
    )
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

    fake_result = MagicMock(
        state="SUCCESS", info={"progress": 1.0, "content_objects": {}}
    )
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
