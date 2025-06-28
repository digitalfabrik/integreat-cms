from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

import pytest
from django.core.management.base import CommandError

from integreat_cms.cms.models import Contact, Event, POI, Region

from ..utils import get_command_output


@pytest.mark.django_db
def test_no_argument_fails() -> None:
    """
    Tests that the command fails when no argument is supplied.
    """
    with pytest.raises(CommandError) as exc_info:
        get_command_output("copy_pois_events_and_contacts")

    assert (
        str(exc_info.value)
        == "Error: the following arguments are required: template_slug, target_slugs"
    )


parameter = [
    (None, None),
    ("--contacts", None),
    (None, "--events"),
    ("--contacts", "--events"),
]


@pytest.mark.parametrize("parameter", parameter)
@pytest.mark.django_db
def test_copy_pois_succeeds(
    load_test_data_transactional: Any | None,
    parameter: tuple[str | None, str | None],
) -> None:
    """
    Tests whether POIs are duplicated as expected
    """

    template_region_slug = "augsburg"
    target_region_slug = "artland"
    contacts_flag, events_flag = parameter

    target_region = Region.objects.get(slug=target_region_slug)
    assert POI.objects.filter(region=target_region).count() == 0
    assert Contact.objects.filter(location__region=target_region).count() == 0
    assert Event.objects.filter(region=target_region).count() == 0

    if contacts_flag and events_flag:
        get_command_output(
            "copy_pois_events_and_contacts",
            template_region_slug,
            target_region_slug,
            contacts_flag,
            events_flag,
        )
    elif contacts_flag:
        get_command_output(
            "copy_pois_events_and_contacts",
            template_region_slug,
            target_region_slug,
            contacts_flag,
        )
    elif events_flag:
        get_command_output(
            "copy_pois_events_and_contacts",
            template_region_slug,
            target_region_slug,
            events_flag,
        )
    else:
        get_command_output(
            "copy_pois_events_and_contacts",
            template_region_slug,
            target_region_slug,
        )
    template_region = Region.objects.get(slug=template_region_slug)
    number_of_pois = POI.objects.filter(region=template_region).count()
    number_of_contacts = (
        Contact.objects.filter(location__region=template_region).count()
        if contacts_flag
        else 0
    )
    number_of_events = (
        Event.objects.filter(region=template_region).count() if events_flag else 0
    )

    assert POI.objects.filter(region=target_region).count() == number_of_pois
    assert (
        Contact.objects.filter(location__region=target_region).count()
        == number_of_contacts
    )
    assert Event.objects.filter(region=target_region).count() == number_of_events
