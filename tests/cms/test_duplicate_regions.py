from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.forms.models import model_to_dict
from django.urls import reverse
from django.utils import timezone
from linkcheck.models import Link

from integreat_cms.cms.constants import status
from integreat_cms.cms.models import LanguageTreeNode, Page, Region

if TYPE_CHECKING:
    from django.test.client import Client


@pytest.mark.order("last")
@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_duplicate_regions(
    load_test_data_transactional: None,
    admin_client: Client,
) -> None:
    """
    Test whether duplicating regions works as expected

    :param load_test_data_transactional: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data_transactional`)
    :param admin_client: The fixture providing the logged in admin (see :fixture:`admin_client`)
    """
    source_region = Region.objects.get(id=1)
    target_region_slug = "cloned"
    assert not Region.objects.filter(
        slug=target_region_slug,
    ).exists(), "The target region should not exist before cloning"

    # Assert correct preconditions for link replacement test
    test_url = "https://integreat.app/augsburg/de/willkommen/"
    assert Link.objects.filter(
        url__url=test_url,
        page_translation__page__region=source_region,
    ).exists(), "The internal test URL should exist in the source region"
    replaced_url = test_url.replace(source_region.slug, target_region_slug)
    assert not Link.objects.filter(
        url__url=replaced_url,
        page_translation__page__region=source_region,
    ).exists(), "The replaced internal URL not should exist in the source region"

    before_cloning = timezone.now()
    url = reverse("new_region")
    response = admin_client.post(
        url,
        data={
            "administrative_division": "CITY",
            "name": "cloned",
            "admin_mail": "cloned@example.com",
            "postal_code": "11111",
            "status": "ACTIVE",
            "longitude": 1,
            "latitude": 1,
            "duplicated_region": 1,
            "duplication_keep_translations": True,
            "duplication_pbo_behavior": "activate_missing",
            "zammad_url": "https://zammad-test.example.com",
            "timezone": "Europe/Berlin",
            "mt_budget_booked": 50000,
            "mt_renewal_month": 6,
            "summ_ai_renewal_month": 6,
        },
    )
    assert response.status_code == 302

    target_region = Region.objects.get(slug="cloned")

    # Check if all cloned pages exist and are identical
    source_pages = source_region.non_archived_pages
    target_pages = target_region.pages.all()
    assert len(source_pages) == len(target_pages)
    for source_page, target_page in zip(source_pages, target_pages, strict=False):
        source_page_dict = model_to_dict(
            source_page,
            exclude=[
                "id",
                "tree_id",
                "region",
                "parent",
                "api_token",
                "authors",
                "editors",
            ],
        )
        target_page_dict = model_to_dict(
            target_page,
            exclude=[
                "id",
                "tree_id",
                "region",
                "parent",
                "api_token",
                "authors",
                "editors",
            ],
        )
        assert source_page_dict == target_page_dict

        # Check if all cloned page translations exist and are identical
        source_page_translations = source_page.translations.all()
        # Limit target page translations to all that existed before the links might have been replaced
        target_page_translations = target_page.translations.filter(
            last_updated__lt=before_cloning,
        )
        assert len(source_page_translations) == len(target_page_translations)
        for source_page_translation, target_page_translation in zip(
            source_page_translations,
            target_page_translations,
            strict=False,
        ):
            source_page_translation_dict = model_to_dict(
                source_page_translation,
                exclude=["id", "page", "status", "hix_score", "hix_feedback"],
            )
            target_page_translation_dict = model_to_dict(
                target_page_translation,
                exclude=["id", "page", "status", "hix_score", "hix_feedback"],
            )
            assert source_page_translation_dict == target_page_translation_dict
            assert target_page_translation.status == status.DRAFT

    # Check if all cloned language tree nodes exist and are identical
    source_language_tree = source_region.language_tree_nodes.all()
    target_language_tree = target_region.language_tree_nodes.all()
    assert len(source_language_tree) == len(target_language_tree)
    for source_node, target_node in zip(
        source_language_tree,
        target_language_tree,
        strict=False,
    ):
        source_node_dict = model_to_dict(
            source_node,
            exclude=["id", "tree_id", "region", "parent"],
        )
        target_node_dict = model_to_dict(
            target_node,
            exclude=["id", "tree_id", "region", "parent"],
        )
        assert source_node_dict == target_node_dict

    # Check for duplicated tree ids
    for model in [LanguageTreeNode, Page]:
        # Make sure each combination of tree_id and lft resp. rgt only exists once
        for tree_field in ["lft", "rgt"]:
            combinations = model.objects.values_list("tree_id", tree_field)
            # Make sure there are no duplicates in this list
            assert len(combinations) == len(set(combinations))
        # Make sure each tree_id only exists in one region
        combinations = model.objects.values_list("tree_id", "region")
        tree_ids = [tree_id for tree_id, region in set(combinations)]
        assert len(tree_ids) == len(set(tree_ids))


@pytest.mark.order("last")
@pytest.mark.django_db(transaction=True, serialized_rollback=True)
def test_duplicate_regions_no_translations(
    load_test_data_transactional: None,
    admin_client: Client,
) -> None:
    """
    Test whether duplicating regions works as expected when disabling the duplication of translations

    :param load_test_data_transactional: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data_transactional`)
    :param admin_client: The fixture providing the logged in admin (see :fixture:`admin_client`)
    """
    source_region = Region.objects.get(id=1)
    target_region_slug = "cloned"
    assert not Region.objects.filter(
        slug=target_region_slug,
    ).exists(), "The target region should not exist before cloning"

    before_cloning = timezone.now()
    url = reverse("new_region")
    response = admin_client.post(
        url,
        data={
            "administrative_division": "CITY",
            "name": "cloned",
            "admin_mail": "cloned@example.com",
            "postal_code": "11111",
            "status": "ACTIVE",
            "longitude": 1,
            "latitude": 1,
            "duplicated_region": 1,
            "duplication_keep_translations": False,
            "duplication_pbo_behavior": "activate_missing",
            "zammad_url": "https://zammad-test.example.com",
            "timezone": "Europe/Berlin",
            "mt_budget_booked": 50000,
            "mt_renewal_month": 6,
            "summ_ai_renewal_month": 6,
        },
    )
    assert response.status_code == 302

    target_region = Region.objects.get(slug="cloned")

    source_language_root = source_region.language_tree_root.language
    target_languages = target_region.languages
    assert len(target_languages) == 1
    assert source_language_root in target_languages

    # Check if all cloned pages exist and are identical
    source_pages = source_region.non_archived_pages
    target_pages = target_region.pages.all()
    assert len(source_pages) == len(target_pages)
    for source_page, target_page in zip(source_pages, target_pages, strict=False):
        source_page_dict = model_to_dict(
            source_page,
            exclude=[
                "id",
                "tree_id",
                "region",
                "parent",
                "api_token",
                "authors",
                "editors",
            ],
        )
        target_page_dict = model_to_dict(
            target_page,
            exclude=[
                "id",
                "tree_id",
                "region",
                "parent",
                "api_token",
                "authors",
                "editors",
            ],
        )
        assert source_page_dict == target_page_dict

        source_page_translations_filtered = source_page.translations.filter(
            language=source_language_root,
        )
        target_page_translations = target_page.translations.filter(
            last_updated__lt=before_cloning,
        )
        assert len(source_page_translations_filtered) == len(target_page_translations)
        assert target_page_translations[0].language == source_language_root
