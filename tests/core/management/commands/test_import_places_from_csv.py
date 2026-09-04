from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from django.core.management.base import CommandError
from geopy.location import Location

from integreat_cms.cms.constants import placecategory, status
from integreat_cms.cms.models import Place, PlaceTranslation, Region
from integreat_cms.nominatim_api.nominatim_api_client import NominatimApiClient

from ..utils import get_command_output

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

CSV_FILE = "tests/core/management/commands/assets/places_to_import.csv"
REGION_SLUG = "augsburg"
USERNAME = "root"
PLACE_NAMES = ["Café Tür an Tür", "Bellevue di Monaco", "Brandenburger Tor"]
MOCKED_COORDINATES = (48.3780446, 10.8879783)
CLOSED = {"timeSlots": [], "allDay": False, "closed": True, "appointmentOnly": False}
ALL_DAY = {"timeSlots": [], "allDay": True, "closed": False, "appointmentOnly": False}
OPEN = {
    "timeSlots": [{"start": "09:00", "end": "17:00"}],
    "allDay": False,
    "closed": False,
    "appointmentOnly": False,
}


@pytest.fixture
def mock_nominatim() -> Generator[None]:
    """
    Mock the Nominatim API to avoid real requests during the import
    """
    location = Location(
        "Mocked address",
        MOCKED_COORDINATES,
        {"address": {"country": "Deutschland"}},
    )
    with patch.object(NominatimApiClient, "search", return_value=location):
        yield


def test_no_argument_fails() -> None:
    """
    Tests that the command fails when no argument is supplied.
    """
    with pytest.raises(CommandError) as exc_info:
        get_command_output("import_places_from_csv")

    assert (
        str(exc_info.value)
        == "Error: the following arguments are required: csv_filename, region_slug, username"
    )


@pytest.mark.django_db
def test_non_existing_region_fails(load_test_data: None) -> None:
    """
    Tests that the command fails when the given region does not exist.
    """
    with pytest.raises(CommandError) as exc_info:
        get_command_output("import_places_from_csv", CSV_FILE, "non-existing", USERNAME)

    assert str(exc_info.value) == 'Region with slug "non-existing" does not exist.'


@pytest.mark.django_db
def test_non_existing_user_fails(load_test_data: None) -> None:
    """
    Tests that the command fails when the given user does not exist.
    """
    with pytest.raises(CommandError) as exc_info:
        get_command_output(
            "import_places_from_csv",
            CSV_FILE,
            REGION_SLUG,
            "non-existing",
        )

    assert str(exc_info.value) == 'User with username "non-existing" does not exist.'


@pytest.mark.django_db
def test_import_successful(load_test_data: None, mock_nominatim: None) -> None:
    """
    Tests that all places of the CSV file are imported as drafts of the region's default language
    """
    region = Region.objects.get(slug=REGION_SLUG)

    assert not PlaceTranslation.objects.filter(
        place__region=region,
        title__in=PLACE_NAMES,
    ).exists(), "Places should not exist before import"

    out, err = get_command_output(
        "import_places_from_csv",
        CSV_FILE,
        REGION_SLUG,
        USERNAME,
    )
    assert not err
    assert f"✔ Imported CSV file {CSV_FILE}" in out

    for name in PLACE_NAMES:
        place_translation = PlaceTranslation.objects.filter(
            place__region=region,
            title=name,
        ).first()
        assert place_translation, f"Place {name!r} should exist after import"
        assert place_translation.language == region.default_language
        assert place_translation.status == status.DRAFT
        assert place_translation.creator.username == USERNAME


@pytest.mark.django_db
def test_import_address_data(load_test_data: None, mock_nominatim: None) -> None:
    """
    Tests that the columns of the CSV file are imported into the correct fields
    """
    get_command_output("import_places_from_csv", CSV_FILE, REGION_SLUG, USERNAME)

    place = Place.objects.get(translations__title=PLACE_NAMES[0])
    assert place.address == "Wertachstr. 29"
    assert place.postcode == "86153"
    assert place.city == "Augsburg"
    # The country is missing in the CSV file and therefore autocompleted by the Nominatim API
    assert place.country == "Deutschland"
    assert (place.latitude, place.longitude) == MOCKED_COORDINATES
    assert place.place_on_map
    assert place.barrier_free
    assert not place.temporarily_closed
    assert (
        Place.objects.get(translations__title=PLACE_NAMES[1]).appointment_url
        == "https://bellevuedimonaco.de/veranstaltungen/"
    )


@pytest.mark.django_db
def test_import_categories(load_test_data: None, mock_nominatim: None) -> None:
    """
    Tests that existing categories are matched by name and unknown ones fall back to the default category
    """
    get_command_output("import_places_from_csv", CSV_FILE, REGION_SLUG, USERNAME)

    icons = [
        Place.objects.get(translations__title=name).category.icon
        for name in PLACE_NAMES
    ]
    # "Gastronomie" exists in the test data, "Sonstiges" and "Treffpunkt" do not,
    # so they fall back to the default category
    assert icons == [placecategory.GASTRONOMY, placecategory.OTHER, placecategory.OTHER]


@pytest.mark.django_db
def test_import_opening_hours(load_test_data: None, mock_nominatim: None) -> None:
    """
    Tests that the opening hour columns are parsed into our JSON structure
    """
    get_command_output("import_places_from_csv", CSV_FILE, REGION_SLUG, USERNAME)

    closed_all_week = [CLOSED] * 7
    # All opening hour columns of this place are empty, so it defaults to closed
    assert (
        Place.objects.get(translations__title=PLACE_NAMES[0]).opening_hours
        == closed_all_week
    )
    # This place is explicitly closed on all days
    assert (
        Place.objects.get(translations__title=PLACE_NAMES[1]).opening_hours
        == closed_all_week
    )
    # This place is open on Monday, Wednesday and Friday, open all day on Tuesday
    # and closed on Thursday and the weekend
    assert Place.objects.get(translations__title=PLACE_NAMES[2]).opening_hours == [
        OPEN,
        ALL_DAY,
        OPEN,
        CLOSED,
        OPEN,
        CLOSED,
        CLOSED,
    ]


@pytest.mark.django_db
def test_import_invalid_csv_fails(
    load_test_data: None,
    mock_nominatim: None,
    tmp_path: Path,
) -> None:
    """
    Tests that the command fails with the form errors if the CSV file contains invalid data
    """
    with open(CSV_FILE, encoding="utf-8") as csv_file:
        lines = csv_file.read().splitlines()
    invalid_csv = tmp_path / "invalid_places.csv"
    invalid_csv.write_text(
        "\n".join([lines[0], lines[1].replace("cafe@tuerantuer.de", "invalid-email")]),
        encoding="utf-8",
    )

    with pytest.raises(CommandError) as exc_info:
        get_command_output(
            "import_places_from_csv",
            str(invalid_csv),
            REGION_SLUG,
            USERNAME,
        )

    assert "Enter a valid email address." in str(exc_info.value)
    assert not PlaceTranslation.objects.filter(title=PLACE_NAMES[0]).exists()
