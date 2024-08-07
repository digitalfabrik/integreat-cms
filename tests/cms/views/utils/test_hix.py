from __future__ import annotations

import math
from copy import deepcopy
from operator import itemgetter
from typing import TYPE_CHECKING

import pytest
from pytest_django.fixtures import SettingsWrapper

from integreat_cms.cms.constants.administrative_division import MUNICIPALITY
from integreat_cms.cms.constants.region_status import ACTIVE
from integreat_cms.cms.models import (
    Language,
    LanguageTreeNode,
    Page,
    PageTranslation,
    Region,
)
from integreat_cms.cms.utils.round_hix_score import round_hix_score
from integreat_cms.cms.views.utils.hix import (
    get_translation_over_hix_threshold,
    get_translation_under_hix_threshold,
    get_translations_relevant_to_hix,
)
from tests.utils import disable_hix_post_save_signal

if TYPE_CHECKING:
    from pytest_django.plugin import _DatabaseBlocker  # type: ignore[attr-defined]


@pytest.fixture(scope="session")
def dummy_region(django_db_setup: None, django_db_blocker: _DatabaseBlocker) -> Region:
    """
    Fixture to create a hix enabled dummy region, along with a dummy language.
    """
    with django_db_blocker.unblock():
        dummy_language = Language.objects.create(
            slug="du",
            bcp47_tag="du_DU",
            primary_country_code="de",
        )
        dummy_language.save()
        dummy_region = Region.objects.create(
            name="HIX Test",
            slug="hix-test",
            status=ACTIVE,
            administrative_division=MUNICIPALITY,
            postal_code="12345",
            admin_mail="admin@example.com",
            hix_enabled=True,
        )
        dummy_region.save()
        dummy_tree_node = LanguageTreeNode.add_root(
            language=dummy_language,
            region=dummy_region,
        )
        dummy_tree_node.save()

    return dummy_region


def test_hix_rounding(settings: SettingsWrapper) -> None:
    HIX_ROUNDING_PRECISION = 0.01
    actual_raw_hix_score_threshold = (
        settings.HIX_REQUIRED_FOR_MT - HIX_ROUNDING_PRECISION / 2
    )
    # Since this will likely differ from the mathematical threshold due to floating point errors,
    # get the nearest value representable in memory as examples for the raw hix score
    hix_score_just_on_threshold = math.nextafter(
        actual_raw_hix_score_threshold, math.inf
    )
    hix_score_just_under_threshold = math.nextafter(
        actual_raw_hix_score_threshold, -math.inf
    )

    assert (
        round_hix_score(hix_score_just_on_threshold) == settings.HIX_REQUIRED_FOR_MT
    ), f"Raw HIX score expected to be accepted: {hix_score_just_on_threshold}"
    assert (
        round_hix_score(hix_score_just_under_threshold) < settings.HIX_REQUIRED_FOR_MT
    ), f"Raw HIX score expected to be rejected: {hix_score_just_under_threshold}"


@pytest.mark.django_db
def test_disregard_archived_pages(
    settings: SettingsWrapper, dummy_region: Region
) -> None:
    dummy_language = dummy_region.default_language
    settings.TEXTLAB_API_LANGUAGES = [dummy_language.slug]

    with disable_hix_post_save_signal():
        page_1 = Page.add_root(
            region=dummy_region,
            explicitly_archived=True,
        )
        page_1.save()

        translation_1 = PageTranslation.objects.create(
            page=page_1,
            hix_score=16.0,
            title="Page 1",
            slug="page-1",
            language=dummy_language,
            content="",
        )
        translation_1.save()

        page_2 = page_1.add_child(
            region=dummy_region,
            # we want a page that is implicitly archived
            explicitly_archived=False,
        )
        page_2.save()

        translation_2 = PageTranslation.objects.create(
            page=page_2,
            hix_score=16.0,
            title="Page 2",
            slug="page-2",
            language=dummy_language,
            content="",
        )
        translation_2.save()

        page_3 = page_1.add_sibling(
            region=dummy_region,
            explicitly_archived=False,
        )
        page_3.save()

        translation_3 = PageTranslation.objects.create(
            page=page_3,
            hix_score=16.0,
            title="Page 3",
            slug="page-3",
            language=dummy_language,
            content="",
        )
        translation_3.save()

    assert set(get_translations_relevant_to_hix(dummy_region)) == {translation_3}
    assert set(get_translation_over_hix_threshold(dummy_region)) == {translation_3}
    assert set(get_translation_under_hix_threshold(dummy_region)) == set()


@pytest.mark.django_db
def test_disregard_pages_with_hix_ignore(
    settings: SettingsWrapper, dummy_region: Region
) -> None:
    dummy_language = dummy_region.default_language
    settings.TEXTLAB_API_LANGUAGES = [dummy_language.slug]

    with disable_hix_post_save_signal():
        page_1 = Page.add_root(
            region=dummy_region,
            hix_ignore=True,
        )
        page_1.save()

        translation_1 = PageTranslation.objects.create(
            page=page_1,
            hix_score=16.0,
            title="Page 1",
            slug="page-1",
            language=dummy_language,
            content="",
        )
        translation_1.save()

        page_2 = page_1.add_child(
            region=dummy_region,
            hix_ignore=False,
        )
        page_2.save()

        translation_2 = PageTranslation.objects.create(
            page=page_2,
            hix_score=16.0,
            title="Page 2",
            slug="page-2",
            language=dummy_language,
            content="",
        )
        translation_2.save()

        page_3 = page_1.add_sibling(
            region=dummy_region,
            hix_ignore=False,
        )
        page_3.save()

        translation_3 = PageTranslation.objects.create(
            page=page_3,
            hix_score=16.0,
            title="Page 3",
            slug="page-3",
            language=dummy_language,
            content="",
        )
        translation_3.save()

    assert set(get_translations_relevant_to_hix(dummy_region)) == {
        translation_2,
        translation_3,
    }
    assert set(get_translation_over_hix_threshold(dummy_region)) == {
        translation_2,
        translation_3,
    }
    assert set(get_translation_under_hix_threshold(dummy_region)) == set()


@pytest.mark.django_db
def test_hix_values(settings: SettingsWrapper, dummy_region: Region) -> None:
    dummy_language = dummy_region.default_language
    settings.TEXTLAB_API_LANGUAGES = [dummy_language.slug]

    HIX_ROUNDING_PRECISION = 0.01
    actual_raw_hix_score_threshold = (
        settings.HIX_REQUIRED_FOR_MT - HIX_ROUNDING_PRECISION / 2
    )
    # Since this will likely differ from the mathematical threshold due to floating point errors,
    # get the nearest value representable in memory as examples for the raw hix score
    hix_score_just_on_threshold = math.nextafter(
        actual_raw_hix_score_threshold, math.inf
    )
    hix_score_just_under_threshold = math.nextafter(
        actual_raw_hix_score_threshold, -math.inf
    )

    with disable_hix_post_save_signal():
        page_1 = Page.add_root(
            region=dummy_region,
        )
        page_1.save()

        translation_1 = PageTranslation.objects.create(
            page=page_1,
            hix_score=0.0,
            title="Page 1",
            slug="page-1",
            language=dummy_language,
            content="",
        )
        translation_1.save()

        page_2 = page_1.add_sibling(
            region=dummy_region,
        )
        page_2.save()

        translation_2 = PageTranslation.objects.create(
            page=page_2,
            hix_score=hix_score_just_under_threshold,
            title="Page 2",
            slug="page-2",
            language=dummy_language,
            content="",
        )
        translation_2.save()

        page_3 = page_2.add_sibling(
            region=dummy_region,
        )
        page_3.save()

        translation_3 = PageTranslation.objects.create(
            page=page_3,
            hix_score=hix_score_just_on_threshold,
            title="Page 2",
            slug="page-2",
            language=dummy_language,
            content="",
        )
        translation_3.save()

    assert set(get_translations_relevant_to_hix(dummy_region)) == {
        translation_1,
        translation_2,
        translation_3,
    }
    assert set(get_translation_over_hix_threshold(dummy_region)) == {translation_3}
    assert set(get_translation_under_hix_threshold(dummy_region)) == {
        translation_1,
        translation_2,
    }


@pytest.mark.django_db
def test_versions_of_hix_page(settings: SettingsWrapper, dummy_region: Region) -> None:
    dummy_language = dummy_region.default_language
    settings.TEXTLAB_API_LANGUAGES = [dummy_language.slug]

    with disable_hix_post_save_signal():
        page = Page.add_root(
            region=dummy_region,
        )
        page.save()

        translation_1 = PageTranslation.objects.create(
            page=page,
            hix_score=5.0,
            title="Version 1",
            slug="page",
            language=dummy_language,
            content="",
            version=1,
        )
        translation_1.save()

        translation_2 = deepcopy(translation_1)
        translation_2.pk = None
        translation_2.title = "Version 2"
        translation_2.version = 2
        translation_2.hix_score = 18.0
        translation_2.save()

        translation_3 = deepcopy(translation_2)
        translation_3.pk = None
        translation_3.title = "Version 3"
        translation_3.version = 3
        translation_3.hix_score = 2.0
        translation_3.save()

    assert set(get_translations_relevant_to_hix(dummy_region)) == {
        translation_3,
    }
    assert set(get_translation_over_hix_threshold(dummy_region)) == set()
    assert set(get_translation_under_hix_threshold(dummy_region)) == {
        translation_3,
    }
