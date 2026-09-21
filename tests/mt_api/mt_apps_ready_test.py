from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from django.apps import apps

if TYPE_CHECKING:
    from django.apps.config import AppConfig

APP_LABELS = ["deepl_api", "google_translate_api"]


@pytest.mark.parametrize("app_label", APP_LABELS)
def test_ready_connects_check_to_worker_process_init_under_celery(
    app_label: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Regression test: the availability check used to run via `celeryd_after_setup`,
    which fires in Celery's main process before the worker pool forks. On
    macOS, a network call made there poisons every forked child's own socket
    connections (segfault, no traceback, unrecoverable) - see PR #4504. The
    check must instead be wired to `worker_process_init`, which runs inside
    each already-forked pool child.
    """
    app_config: AppConfig = apps.get_app_config(app_label)
    monkeypatch.setattr("sys.argv", ["celery"])
    monkeypatch.delenv("APACHE_PID_FILE", raising=False)

    with (
        patch("celery.signals.worker_process_init") as mock_worker_process_init,
        patch("celery.signals.celeryd_after_setup") as mock_celeryd_after_setup,
    ):
        app_config.ready()

    mock_worker_process_init.connect.assert_called_once_with(
        app_config._check_availability_on_celery_ready,  # type: ignore[attr-defined]
        weak=False,
    )
    mock_celeryd_after_setup.connect.assert_not_called()


@pytest.mark.parametrize("app_label", APP_LABELS)
def test_ready_checks_immediately_under_runserver(
    app_label: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app_config: AppConfig = apps.get_app_config(app_label)
    monkeypatch.setattr("sys.argv", ["manage.py", "runserver"])

    with patch.object(app_config, "check_availability") as mock_check_availability:
        app_config.ready()

    mock_check_availability.assert_called_once_with()
