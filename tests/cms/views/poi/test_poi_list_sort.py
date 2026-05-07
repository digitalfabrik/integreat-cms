from __future__ import annotations

import pytest
from django.test import RequestFactory

from integreat_cms.cms.constants import status
from integreat_cms.cms.models import Language, POITranslation, Region
from integreat_cms.cms.views.pois.poi_list_view import POIListView

REGION_SLUG = "augsburg"
LANGUAGE_SLUG = "de"

# Augsburg POIs visible in the unarchived list (region 1, language de):
#   pk=4 "Test-Ort"    PUBLIC  — also has en + ar translations
#   pk=6 "Entwurf-Ort" DRAFT   — also has an en translation
POI_TEST_ORT = 4
POI_ENTWURF_ORT = 6


def _sorted_poi_ids(sort_param: str) -> list[int]:
    """Run the list view's sort/filter logic and return the ordered POI ids."""
    view = POIListView()
    view.request = RequestFactory().get("/", {"sort": sort_param})
    view.kwargs = {"language_slug": LANGUAGE_SLUG}

    region = Region.objects.get(slug=REGION_SLUG)
    queryset = region.pois.filter(archived=False)
    return list(
        view.get_filtered_sorted_queryset(queryset).values_list("pk", flat=True),
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "sort_param,expected_order",
    [
        ("_sort_title", [POI_ENTWURF_ORT, POI_TEST_ORT]),
        ("-_sort_title", [POI_TEST_ORT, POI_ENTWURF_ORT]),
    ],
)
def test_poi_list_sort_by_title_does_not_duplicate_translations(
    load_test_data: None,
    sort_param: str,
    expected_order: list[int],
) -> None:
    """
    Sorting through the reverse FK ``translations`` used to JOIN and produce one row
    per (POI, translation), so a POI with N translations appeared N times. POI 4 has
    three translations (de/en/ar); the buggy ordering returned [6, 6, 4, 4, 4, 4].
    The fix annotates a Subquery over the latest translation in the URL language and
    orders by that — exactly the title rendered by the row template.
    """
    assert _sorted_poi_ids(sort_param) == expected_order


@pytest.mark.django_db
def test_poi_list_sort_by_status_uses_workflow_order(load_test_data: None) -> None:
    """
    Status sorting must follow the workflow order
    (DRAFT < REVIEW < PUBLIC < AUTO_SAVE), not the lexicographic order of the choice
    keys (where AUTO_SAVE < DRAFT < PUBLIC < REVIEW). Promote POI 6's latest DE
    translation to REVIEW so the two POIs differ on a status pair where workflow and
    alphabetic orderings disagree (REVIEW < PUBLIC by workflow, PUBLIC < REVIEW
    alphabetically).
    """
    POITranslation.objects.create(
        poi_id=POI_ENTWURF_ORT,
        language=Language.objects.get(slug=LANGUAGE_SLUG),
        title="Entwurf-Ort",
        slug="entwurf-ort",
        status=status.REVIEW,
        version=2,
        content="",
    )

    # workflow asc: REVIEW(rank 1) = POI 6 < PUBLIC(rank 2) = POI 4
    # alphabetic asc would give the opposite: PUBLIC < REVIEW → [4, 6]
    assert _sorted_poi_ids("_sort_status") == [POI_ENTWURF_ORT, POI_TEST_ORT]
