from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture
    from django.test.client import Client
    from pytest_django.fixtures import SettingsWrapper

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from integreat_cms.cms.models import Language, LanguageTreeNode, Region
from tests.cms.views.bulk_actions import assert_bulk_delete, BulkActionIDs


def create_language_tree_node(
    region_slug: str,
    language_id: int,
    parent: LanguageTreeNode | None = None,
) -> int:
    """
    A helper function to create a Language Tree Node

    Returns the language tree node ID
    """
    region = Region.objects.get(slug=region_slug)
    ltn = LanguageTreeNode.add_root(
        region=region, language=Language.objects.get(id=language_id), parent=parent
    )
    return ltn.id


def create_language_tree_node_with_children(
    region_slug: str,
    language_id: int,
    num_children: int = 2,
    start_lft: int = 1,
    tree_id: int = 1,
) -> int:
    """
    A helper function to create a root languageTreeNode with `num_children` child languageTreeNodes

    Returns the root ID.
    """
    region = Region.objects.get(slug=region_slug)
    # Create root node
    root_ltn = LanguageTreeNode.add_root(
        region=region,
        language=Language.objects.get(id=language_id),
        parent=None,
    )

    for i in range(num_children):
        root_ltn.add_child(
            region=region,
            language=Language.objects.get(id=language_id + i + 1),
            parent=root_ltn,
        )

    return root_ltn.id


@pytest.mark.django_db
@pytest.mark.parametrize("role", ["ROOT", "AUTHOR"])
@pytest.mark.parametrize(
    "num_deletable, num_undeletable",
    [
        pytest.param(1, 1, id="deletable_node=1_undeletable_node=1"),
        pytest.param(2, 0, id="deletable_nodes=2"),
        pytest.param(0, 2, id="undeletable_nodes=2"),
        pytest.param(2, 2, id="deletable_nodes=2_undeletable_nodes=2"),
    ],
)
def test_bulk_delete_language_tree_nodes(
    role: str,
    client: Client,
    load_test_data: None,
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
    num_deletable: int,
    num_undeletable: int,
) -> None:
    """
    Test whether bulk deleting of pois works as expected
    """
    user = get_user_model().objects.get(username=role.lower())
    client.force_login(user)

    deletable_nodes = [
        create_language_tree_node("empty-region", language_id=i + 1)
        for i in range(num_deletable)
    ]
    undeletable_nodes = [
        create_language_tree_node_with_children(
            "empty-region", language_id=i * 2 + 1 + num_deletable, num_children=1
        )
        for i in range(num_undeletable)
    ]
    instance_ids: BulkActionIDs = {
        "deletable": deletable_nodes,
        "undeletable": [undeletable_nodes],
    }
    fail_reason = ["a source language of other language(s) cannot be deleted."]
    url = reverse(
        "bulk_delete_languagetreenodes",
        kwargs={"region_slug": "empty-region"},
    )
    assert_bulk_delete(
        LanguageTreeNode,
        instance_ids,
        url,
        (client, role),
        caplog,
        settings,
        fail_reason,
    )
