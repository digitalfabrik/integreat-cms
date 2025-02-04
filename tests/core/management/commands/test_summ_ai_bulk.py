from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.core.management.base import CommandError

from integreat_cms.cms.models import Region

from ..utils import get_command_output

if TYPE_CHECKING:
    from pytest_django.fixtures import SettingsWrapper


def test_summ_ai_bulk_missing_args() -> None:
    """
    Ensure that missing args cause an error
    """
    with pytest.raises(CommandError) as exc_info:
        assert not any(get_command_output("summ_ai_bulk"))
    assert (
        str(exc_info.value)
        == "Error: the following arguments are required: region_slug, username"
    )


def test_summ_ai_bulk_missing_username() -> None:
    """
    Ensure that a missing username throws an error
    """
    with pytest.raises(CommandError) as exc_info:
        assert not any(get_command_output("summ_ai_bulk", "region_slug"))
    assert (
        str(exc_info.value) == "Error: the following arguments are required: username"
    )


@pytest.mark.django_db
def test_summ_ai_bulk_disabled(settings: SettingsWrapper, load_test_data: None) -> None:
    """
    Ensure that calling when globally disabled throws an error
    """
    settings.SUMM_AI_ENABLED = False
    with pytest.raises(CommandError) as exc_info:
        assert not any(get_command_output("summ_ai_bulk", "augsburg", "username"))
    assert str(exc_info.value) == "SUMM.AI API is disabled globally."


@pytest.mark.django_db
def test_summ_ai_bulk_non_existing_region() -> None:
    """
    Ensure that a non existing region slug throws an error
    """
    with pytest.raises(CommandError) as exc_info:
        assert not any(get_command_output("summ_ai_bulk", "non-existing", "username"))
    assert str(exc_info.value) == 'Region with slug "non-existing" does not exist.'


@pytest.mark.django_db
def test_summ_ai_bulk_disabled_region(load_test_data: None) -> None:
    """
    Ensure that calling when disabled in a region throws an error
    """
    # TODO(timobrembeck): Ensure there are no race conditions with tests.summ_ai_api.summ.ai_test module
    # https://github.com/digitalfabrik/integreat-cms/issues/2119
    #
    # with pytest.raises(CommandError) as exc_info:
    #    assert not any(get_command_output("summ_ai_bulk", "augsburg", "non-existing"))  # noqa: ERA001
    # assert str(exc_info.value) == 'SUMM.AI API is disabled in "Stadt Augsburg".'  # noqa: ERA001


@pytest.mark.django_db
def test_summ_ai_bulk_non_existing_username(load_test_data: None) -> None:
    """
    Ensure that a non existing username throws an error
    """
    region_slug = "augsburg"
    Region.objects.filter(slug=region_slug).update(summ_ai_enabled=True)
    with pytest.raises(CommandError) as exc_info:
        assert not any(get_command_output("summ_ai_bulk", region_slug, "non-existing"))
    assert str(exc_info.value) == 'User with username "non-existing" does not exist.'
