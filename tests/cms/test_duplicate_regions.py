import pytest

from django.forms.models import model_to_dict
from django.urls import reverse

from integreat_cms.cms.constants import status
from integreat_cms.cms.models import Region, LanguageTreeNode, Page

# pylint: disable=unused-argument,too-many-locals
@pytest.mark.django_db
def test_duplicate_regions(load_test_data, admin_client):
    """
    Test whether duplicating regions works as expected

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :type load_test_data: tuple

    :param admin_client: The fixture providing the logged in admin
    :type admin_client: :fixture:`admin_client`
    """
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
            "timezone": "Europe/Berlin",
        },
    )
    print(response.headers)
    assert response.status_code == 302

    source_region = Region.objects.get(id=1)
    target_region = Region.objects.get(slug="cloned")

    # Check if all cloned pages exist and are identical
    source_pages = source_region.pages.all()
    target_pages = target_region.pages.all()
    assert len(source_pages) == len(target_pages)
    for source_page, target_page in zip(source_pages, target_pages):
        source_page_dict = model_to_dict(
            source_page, exclude=["id", "tree_id", "region", "parent", "api_token"]
        )
        target_page_dict = model_to_dict(
            target_page, exclude=["id", "tree_id", "region", "parent", "api_token"]
        )
        assert source_page_dict == target_page_dict

        # Check if all cloned page translations exist and are identical
        source_page_translations = source_page.translations.all()
        target_pages_translations = target_page.translations.all()
        assert len(source_page_translations) == len(target_pages_translations)
        for source_page_translation, target_page_translation in zip(
            source_page_translations, target_pages_translations
        ):
            source_page_translation_dict = model_to_dict(
                source_page_translation, exclude=["id", "page", "status"]
            )
            target_page_translation_dict = model_to_dict(
                target_page_translation, exclude=["id", "page", "status"]
            )
            assert source_page_translation_dict == target_page_translation_dict
            assert target_page_translation.status == status.DRAFT

    # Check if all cloned language tree nodes exist and are identical
    source_language_tree = source_region.language_tree_nodes.all()
    target_language_tree = target_region.language_tree_nodes.all()
    assert len(source_language_tree) == len(target_language_tree)
    for source_node, target_node in zip(source_language_tree, target_language_tree):
        source_node_dict = model_to_dict(
            source_node, exclude=["id", "tree_id", "region", "parent"]
        )
        target_node_dict = model_to_dict(
            target_node, exclude=["id", "tree_id", "region", "parent"]
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
