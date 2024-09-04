from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from integreat_cms.cms.constants.administrative_division import MUNICIPALITY
from integreat_cms.cms.constants.region_status import ACTIVE
from integreat_cms.cms.models import (
    Language,
    LanguageTreeNode,
    Page,
    PageTranslation,
    Region,
)

from ...utils import disable_hix_post_save_signal

if TYPE_CHECKING:
    from pytest_django.plugin import _DatabaseBlocker  # type: ignore[attr-defined]


@pytest.fixture(scope="session")
def dummy_region(django_db_setup: None, django_db_blocker: _DatabaseBlocker) -> Region:
    """
    Fixture to create a dummy region, along with a dummy language.
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
            hix_enabled=False,
        )
        dummy_region.save()
        dummy_tree_node = LanguageTreeNode.add_root(
            language=dummy_language,
            region=dummy_region,
        )
        dummy_tree_node.save()

    return dummy_region


# pylint: disable=redefined-outer-name
@pytest.mark.skip(reason="disabled to avoid failing test to merge a hot fix in #2974")
@pytest.mark.django_db
def test_disable_hix_post_save_signal(dummy_region: Region) -> None:
    with disable_hix_post_save_signal():
        demo_page_translation = create_dummy_page_translation(dummy_region)

    assert demo_page_translation.hix_score == 16


@pytest.mark.skip(reason="disabled to avoid failing test to merge a hot fix in #2974")
@pytest.mark.django_db
def test_rule_out_false_positive(dummy_region: Region) -> None:
    demo_page_translation = create_dummy_page_translation(dummy_region)

    assert demo_page_translation.hix_score is None


def create_dummy_page_translation(dummy_region: Region) -> PageTranslation:
    dummy_page = Page.add_root(region=dummy_region)
    dummy_page.save()

    dummy_page_translation = PageTranslation.objects.create(
        page=dummy_page,
        slug="dummy_page",
        title="Dummy Page",
        content="",
        hix_score=16.0,
        language=dummy_region.default_language,
    )
    dummy_page_translation.save()

    return dummy_page_translation
