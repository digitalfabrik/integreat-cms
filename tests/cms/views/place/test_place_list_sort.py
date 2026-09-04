from __future__ import annotations

import pytest
from django.test import RequestFactory

from integreat_cms.cms.constants import status
from integreat_cms.cms.models import Language, PlaceTranslation, Region
from integreat_cms.cms.views.places.place_list_view import PlaceListView

REGION_SLUG = "augsburg"
LANGUAGE_SLUG = "de"

# Augsburg places visible in the unarchived list (region 1, language de):
#   pk=4 "Test-Ort"    PUBLIC  — also has en + ar translations
#   pk=6 "Entwurf-Ort" DRAFT   — also has an en translation
PLACE_TEST_ORT = 4
PLACE_ENTWURF_ORT = 6


def _sorted_place_ids(sort_param: str) -> list[int]:
    """Run the list view's sort/filter logic and return the ordered place ids."""
    view = PlaceListView()
    view.request = RequestFactory().get("/", {"sort": sort_param})
    view.kwargs = {"language_slug": LANGUAGE_SLUG}

    region = Region.objects.get(slug=REGION_SLUG)
    queryset = region.places.filter(archived=False)
    return list(
        view.get_filtered_sorted_queryset(queryset).values_list("pk", flat=True),
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "sort_param,expected_order",
    [
        ("_sort_title", [PLACE_ENTWURF_ORT, PLACE_TEST_ORT]),
        ("-_sort_title", [PLACE_TEST_ORT, PLACE_ENTWURF_ORT]),
    ],
)
def test_place_list_sort_by_title_does_not_duplicate_translations(
    load_test_data: None,
    sort_param: str,
    expected_order: list[int],
) -> None:
    """
    Sorting through the reverse FK ``translations`` used to JOIN and produce one row
    per (Place, translation), so a place with N translations appeared N times. Place 4 has
    three translations (de/en/ar); the buggy ordering returned [6, 6, 4, 4, 4, 4].
    The fix annotates a Subquery over the latest translation in the URL language and
    orders by that — exactly the title rendered by the row template.
    """
    assert _sorted_place_ids(sort_param) == expected_order


@pytest.mark.django_db
def test_place_list_sort_by_status_uses_workflow_order(load_test_data: None) -> None:
    """
    Status sorting must follow the workflow order
    (DRAFT < REVIEW < PUBLIC < AUTO_SAVE), not the lexicographic order of the choice
    keys (where AUTO_SAVE < DRAFT < PUBLIC < REVIEW). Promote place 6's latest DE
    translation to REVIEW so the two places differ on a status pair where workflow and
    alphabetic orderings disagree (REVIEW < PUBLIC by workflow, PUBLIC < REVIEW
    alphabetically).
    """
    PlaceTranslation.objects.create(
        place_id=PLACE_ENTWURF_ORT,
        language=Language.objects.get(slug=LANGUAGE_SLUG),
        title="Entwurf-Ort",
        slug="entwurf-ort",
        status=status.REVIEW,
        version=2,
        content="",
    )

    # workflow asc: REVIEW(rank 1) = Place 6 < PUBLIC(rank 2) = Place 4
    # alphabetic asc would give the opposite: PUBLIC < REVIEW → [4, 6]
    assert _sorted_place_ids("_sort_status") == [PLACE_ENTWURF_ORT, PLACE_TEST_ORT]
