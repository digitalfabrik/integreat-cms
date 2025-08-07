from __future__ import annotations

import itertools

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
        get_command_output("copy_pois")

    assert (
        str(exc_info.value)
        == "Error: the following arguments are required: template-slug, target-slug"
    )


flags = (
    "--contacts",
    "--events",
    "--add-suffix",
)
# create all possible flag combinations, from none to all of them
parameters = tuple(
    itertools.chain(
        *[
            itertools.combinations(flags, r)
            for r in range(len(flags) + 1)  # up to how many there are + zero
        ]
    )
)


@pytest.mark.parametrize(
    "parameters", parameters, ids=[" ".join(x) for x in parameters]
)
@pytest.mark.django_db
def test_copy_pois_succeeds(
    load_test_data_transactional: None,
    parameters: tuple[str],
) -> None:
    """
    Tests whether POIs are duplicated as expected
    """
    template_region_slug = "augsburg"
    target_region_slug = "artland"

    target_region = Region.objects.get(slug=target_region_slug)
    original_number_of_pois = POI.objects.filter(region=target_region).count()
    original_number_of_contacts = Contact.objects.filter(
        location__region=target_region
    ).count()
    original_number_of_events = Event.objects.filter(region=target_region).count()

    get_command_output(
        "copy_pois", template_region_slug, target_region_slug, *parameters
    )
    template_region = Region.objects.get(slug=template_region_slug)
    number_of_pois = POI.objects.filter(region=template_region).count()
    number_of_contacts = (
        Contact.objects.filter(location__region=template_region).count()
        if "--contacts" in parameters
        else 0
    )
    number_of_events = (
        Event.objects.filter(region=template_region).count()
        if "--events" in parameters
        else 0
    )
    # Ensure test is valid with the given template region
    if number_of_pois == 0:
        pytest.skip("No pois in template region, invalid test")
    if "--contacts" in parameters and number_of_contacts == 0:
        pytest.skip("No contacts in template region, invalid test")
    if "--events" in parameters and number_of_events == 0:
        pytest.skip("No events in template region, invalid test")

    assert (
        POI.objects.filter(region=target_region).count()
        == original_number_of_pois + number_of_pois
    )
    assert (
        Contact.objects.filter(location__region=target_region).count()
        == original_number_of_contacts + number_of_contacts
    )
    assert (
        Event.objects.filter(region=target_region).count()
        == original_number_of_events + number_of_events
    )
