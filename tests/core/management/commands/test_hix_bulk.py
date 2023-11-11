from __future__ import annotations

import pytest
from django.core.management.base import CommandError
from pytest_django.fixtures import SettingsWrapper

from ..utils import get_command_output


@pytest.mark.django_db
def test_hix_bulk_textlab_api_disabled(settings: SettingsWrapper) -> None:
    """
    Ensure that a disabled textlab api causes an error
    """
    settings.TEXTLAB_API_ENABLED = False
    with pytest.raises(CommandError) as exc_info:
        assert not any(get_command_output("hix_bulk"))
    assert str(exc_info.value) == "HIX API is globally disabled"


@pytest.mark.django_db
def test_hix_bulk_bulk_non_existing_region(settings: SettingsWrapper) -> None:
    """
    Ensure that a non existing region slug throws an error
    """
    settings.TEXTLAB_API_ENABLED = True
    with pytest.raises(CommandError) as exc_info:
        assert not any(get_command_output("hix_bulk", "non-existing"))
    assert str(exc_info.value) == "The following regions do not exist: {'non-existing'}"
