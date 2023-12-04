from __future__ import annotations

import pytest
from django.core.management.base import CommandError
from pytest_django.fixtures import SettingsWrapper

from ..utils import get_command_output


@pytest.mark.django_db
def test_push_notifications_disabled(settings: SettingsWrapper) -> None:
    """
    Ensure that disabled push notifications cause an error
    """
    settings.FCM_ENABLED = False
    with pytest.raises(CommandError) as exc_info:
        assert not any(get_command_output("send_push_notifications"))
    assert str(exc_info.value) == "Push notifications are disabled"


@pytest.mark.django_db
def test_push_notifications_nonexisting_testregion(settings: SettingsWrapper) -> None:
    """
    Ensure that an error is caused when the system runs in debug mode but the test region does not exist
    """
    settings.TEST_REGION_SLUG = "non-existing"
    settings.DEBUG = True
    with pytest.raises(CommandError) as exc_info:
        assert not any(get_command_output("send_push_notifications"))
    assert (
        str(exc_info.value)
        == f"The system runs with DEBUG=True but the region with TEST_REGION_SLUG={settings.TEST_REGION_SLUG} does not exist."
    )
