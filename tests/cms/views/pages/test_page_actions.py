from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture
    from django.test.client import Client
    from pytest_django.fixtures import SettingsWrapper

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from integreat_cms.cms.constants import status
from integreat_cms.cms.models import Page, PageTranslation, Region
from tests.cms.views.bulk_actions import bulk_delete, BulkActionIDs


def create_page(
    region_slug: str,
    lft: int,
    rgt: int,
    tree_id: int,
    depth: int,
    name_add: str = "",
    parent: Page | None = None,
) -> int:
    """
    A helper function to create a page

    Returns the page ID
    """
    region = Region.objects.get(slug=region_slug)
    page = Page.objects.create(
        region=region,
        parent=parent,
        lft=lft,
        rgt=rgt,
        tree_id=tree_id,
        depth=depth,
    )
    PageTranslation.objects.create(
        page=page,
        language=region.default_language,
        title="Test Page" + name_add,
        slug="test-page" + name_add,
        status=status.PUBLIC,
    )
    return page.id


def create_page_with_children(
    region_slug: str,
    root_name_add: str = "",
    num_children: int = 2,
    start_lft: int = 1,
    tree_id: int = 1,
) -> tuple[int, int]:
    """
    A helper function to create a root page with `num_children` child pages, manually assigning tree structure.

    Returns the root page ID and the parents rgt.
    """
    depth = 1
    root_rgt = start_lft + (num_children + 1) * 2 - 1

    region = Region.objects.get(slug=region_slug)

    # Create root node
    root_page = Page.objects.create(
        region=region,
        parent=None,
        lft=start_lft,
        rgt=root_rgt,
        tree_id=tree_id,
        depth=depth,
    )

    PageTranslation.objects.create(
        page=root_page,
        language=root_page.region.default_language,
        title=f"Root Page{root_name_add}",
        slug=f"root-page{root_name_add}",
        status=status.PUBLIC,
    )

    # Children start right after root's lft
    child_lft = start_lft + 1
    for i in range(num_children):
        Page.objects.create(
            region=root_page.region,
            parent=root_page,
            lft=child_lft,
            rgt=child_lft + 1,
            tree_id=tree_id,
            depth=depth + 1,
        )
        PageTranslation.objects.create(
            page=root_page.children.last(),
            language=root_page.region.default_language,
            title=f"Child {i}{root_name_add}",
            slug=f"child-{i}{root_name_add}",
            status=status.PUBLIC,
        )
        child_lft += 2

    return root_page.id, root_rgt


def create_page_with_mirror(
    region_slug: str,
    name_add: str = "",
    start_lft: int = 1,
    tree_id: int = 1,
) -> tuple[int, int]:
    """
    A helper function to create a test page with a mirror page

    Returns the page ID and the mirrored page ID
    """
    region = Region.objects.get(slug=region_slug)
    original_page = Page.objects.get(
        id=create_page(
            region_slug,
            name_add=f"{name_add}-original",
            lft=start_lft,
            rgt=start_lft + 1,
            tree_id=tree_id,
            depth=1,
        )
    )

    mirrored_page = Page.objects.create(
        region=region,
        mirrored_page=original_page,
        mirrored_page_first=True,
        tree_id=tree_id + 1,
        lft=start_lft,
        rgt=start_lft + 1,
        depth=1,
    )

    PageTranslation.objects.create(
        page=mirrored_page,
        language=region.default_language,
        title="Mirrored Page" + name_add,
        slug="mirrored-page" + name_add,
        status=status.PUBLIC,
    )
    return original_page.id, mirrored_page.id


@pytest.mark.django_db
@pytest.mark.parametrize("role", ["ROOT", "AUTHOR"])
@pytest.mark.parametrize(
    "num_allowed, num_blocked_1, num_blocked_2",
    [
        (1, 1, 1),
        (2, 0, 0),
        (0, 2, 2),
        (2, 2, 2),
    ],
)
def test_bulk_delete_pages(
    role: str,
    client: Client,
    load_test_data: None,
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
    num_allowed: int,
    num_blocked_1: int,
    num_blocked_2: int,
) -> None:
    """
    Test whether bulk deleting of pois works as expected
    """
    user = get_user_model().objects.get(username=role.lower())
    client.force_login(user)

    allowed_pages = [
        create_page(
            "augsburg",
            lft=2 * i + 1,
            rgt=2 * i + 2,
            depth=1,
            tree_id=20,
            name_add=f"-{i}",
        )
        for i in range(num_allowed)
    ]
    not_allowed_pages_1 = [
        create_page_with_mirror(
            region_slug="augsburg",
            name_add=f"-{i}",
            start_lft=num_allowed * 2 + i * 2 + 1,
            tree_id=20,
        )[0]
        for i in range(num_blocked_1)
    ]
    not_allowed_pages_2 = [
        create_page_with_children(
            region_slug="augsburg",
            root_name_add=f"-{i}",
            num_children=1,
            tree_id=20,
            start_lft=num_allowed * 2 + num_blocked_1 * 2 + i * 4 + 3,
        )[0]
        for i in range(num_blocked_2)
    ]
    instance_ids: BulkActionIDs = {
        "allowed": allowed_pages,
        "not_allowed": [not_allowed_pages_1, not_allowed_pages_2],
    }
    fail_reason = [
        "it was embedded as live content from another page.",
        "you cannot delete a page which has subpages.",
    ]
    url = reverse(
        "bulk_delete_pages",
        kwargs={"region_slug": "augsburg", "language_slug": "en"},
    )
    bulk_delete(Page, instance_ids, url, (client, role), caplog, settings, fail_reason)
