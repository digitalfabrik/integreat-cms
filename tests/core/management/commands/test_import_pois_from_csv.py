from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from django.core.management.base import CommandError
from geopy.location import Location

from integreat_cms.cms.constants import poicategory, status
from integreat_cms.cms.models import POI, POITranslation, Region
from integreat_cms.nominatim_api.nominatim_api_client import NominatimApiClient

from ..utils import get_command_output

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

CSV_FILE = "tests/core/management/commands/assets/pois_to_import.csv"
REGION_SLUG = "augsburg"
USERNAME = "root"
POI_NAMES = ["Café Tür an Tür", "Bellevue di Monaco", "Brandenburger Tor"]
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
        get_command_output("import_pois_from_csv")

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
        get_command_output("import_pois_from_csv", CSV_FILE, "non-existing", USERNAME)

    assert str(exc_info.value) == 'Region with slug "non-existing" does not exist.'


@pytest.mark.django_db
def test_non_existing_user_fails(load_test_data: None) -> None:
    """
    Tests that the command fails when the given user does not exist.
    """
    with pytest.raises(CommandError) as exc_info:
        get_command_output(
            "import_pois_from_csv",
            CSV_FILE,
            REGION_SLUG,
            "non-existing",
        )

    assert str(exc_info.value) == 'User with username "non-existing" does not exist.'


@pytest.mark.django_db
def test_import_successful(load_test_data: None, mock_nominatim: None) -> None:
    """
    Tests that all POIs of the CSV file are imported as drafts of the region's default language
    """
    region = Region.objects.get(slug=REGION_SLUG)

    assert not POITranslation.objects.filter(
        poi__region=region,
        title__in=POI_NAMES,
    ).exists(), "POIs should not exist before import"

    out, err = get_command_output(
        "import_pois_from_csv",
        CSV_FILE,
        REGION_SLUG,
        USERNAME,
    )
    assert not err
    assert f"✔ Imported CSV file {CSV_FILE}" in out

    for name in POI_NAMES:
        poi_translation = POITranslation.objects.filter(
            poi__region=region,
            title=name,
        ).first()
        assert poi_translation, f"POI {name!r} should exist after import"
        assert poi_translation.language == region.default_language
        assert poi_translation.status == status.DRAFT
        assert poi_translation.creator.username == USERNAME


@pytest.mark.django_db
def test_import_address_data(load_test_data: None, mock_nominatim: None) -> None:
    """
    Tests that the columns of the CSV file are imported into the correct fields
    """
    get_command_output("import_pois_from_csv", CSV_FILE, REGION_SLUG, USERNAME)

    poi = POI.objects.get(translations__title=POI_NAMES[0])
    assert poi.address == "Wertachstr. 29"
    assert poi.postcode == "86153"
    assert poi.city == "Augsburg"
    # The country is missing in the CSV file and therefore autocompleted by the Nominatim API
    assert poi.country == "Deutschland"
    assert (poi.latitude, poi.longitude) == MOCKED_COORDINATES
    assert poi.location_on_map
    assert poi.barrier_free
    assert not poi.temporarily_closed
    assert (
        POI.objects.get(translations__title=POI_NAMES[1]).appointment_url
        == "https://bellevuedimonaco.de/veranstaltungen/"
    )


@pytest.mark.django_db
def test_import_categories(load_test_data: None, mock_nominatim: None) -> None:
    """
    Tests that existing categories are matched by name and unknown ones fall back to the default category
    """
    get_command_output("import_pois_from_csv", CSV_FILE, REGION_SLUG, USERNAME)

    icons = [
        POI.objects.get(translations__title=name).category.icon for name in POI_NAMES
    ]
    # "Gastronomie" exists in the test data, "Sonstiges" and "Treffpunkt" do not,
    # so they fall back to the default category
    assert icons == [poicategory.GASTRONOMY, poicategory.OTHER, poicategory.OTHER]


@pytest.mark.django_db
def test_import_opening_hours(load_test_data: None, mock_nominatim: None) -> None:
    """
    Tests that the opening hour columns are parsed into our JSON structure
    """
    get_command_output("import_pois_from_csv", CSV_FILE, REGION_SLUG, USERNAME)

    closed_all_week = [CLOSED] * 7
    # All opening hour columns of this POI are empty, so it defaults to closed
    assert (
        POI.objects.get(translations__title=POI_NAMES[0]).opening_hours
        == closed_all_week
    )
    # This POI is explicitly closed on all days
    assert (
        POI.objects.get(translations__title=POI_NAMES[1]).opening_hours
        == closed_all_week
    )
    # This POI is open on Monday, Wednesday and Friday, open all day on Tuesday
    # and closed on Thursday and the weekend
    assert POI.objects.get(translations__title=POI_NAMES[2]).opening_hours == [
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
    invalid_csv = tmp_path / "invalid_pois.csv"
    invalid_csv.write_text(
        "\n".join([lines[0], lines[1].replace("cafe@tuerantuer.de", "invalid-email")]),
        encoding="utf-8",
    )

    with pytest.raises(CommandError) as exc_info:
        get_command_output(
            "import_pois_from_csv",
            str(invalid_csv),
            REGION_SLUG,
            USERNAME,
        )

    assert "Enter a valid email address." in str(exc_info.value)
    assert not POITranslation.objects.filter(title=POI_NAMES[0]).exists()
