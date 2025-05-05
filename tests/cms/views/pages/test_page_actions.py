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
from tests.cms.views.bulk_actions import assert_bulk_delete, BulkActionIDs


def create_page(
    region_slug: str,
    name_add: str = "",
    parent: Page | None = None,
) -> int:
    """
    A helper function to create a page

    Returns the page ID
    """
    region = Region.objects.get(slug=region_slug)
    page = parent.add_child(region=region) if parent else Page.add_root(region=region)

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
) -> int:
    """
    A helper function to create a root page with `num_children` child pages, manually assigning tree structure.

    Returns the root page ID and the parents rgt.
    """

    region = Region.objects.get(slug=region_slug)

    # Create root node
    root_page = Page.add_root(
        region=region,
    )

    PageTranslation.objects.create(
        page=root_page,
        language=root_page.region.default_language,
        title=f"Root Page{root_name_add}",
        slug=f"root-page{root_name_add}",
        status=status.PUBLIC,
    )

    for i in range(num_children):
        print("creating child page")
        child_page = root_page.add_child(region=root_page.region, parent=root_page)
        PageTranslation.objects.create(
            page=child_page,
            language=root_page.region.default_language,
            title=f"Child {i}{root_name_add}",
            slug=f"child-{i}{root_name_add}",
            status=status.PUBLIC,
        )

    return root_page.id


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
        )
    )

    mirrored_page = Page.add_root(
        region=region,
        mirrored_page=original_page,
        mirrored_page_first=True,
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
    "num_deletable, num_undeletable_1, num_undeletable_2",
    [
        pytest.param(
            1, 1, 1, id="deletable_page=1-page_with_children=1-page_with_mirror=1"
        ),
        pytest.param(2, 0, 0, id="deletable_pages=2"),
        pytest.param(0, 2, 2, id="pages_with_children=2-pages_with_mirror=2"),
        pytest.param(
            2, 2, 2, id="deletable_pages=2-pages_with_children=2-pages_with_mirror=2"
        ),
    ],
)
def test_bulk_delete_pages(
    role: str,
    client: Client,
    load_test_data: None,
    settings: SettingsWrapper,
    caplog: LogCaptureFixture,
    num_deletable: int,
    num_undeletable_1: int,
    num_undeletable_2: int,
) -> None:
    """
    Test whether bulk deleting of pois works as expected
    """
    user = get_user_model().objects.get(username=role.lower())
    client.force_login(user)

    deletable_pages = [
        create_page(
            "augsburg",
            name_add=f"-{i}",
        )
        for i in range(num_deletable)
    ]
    undeletable_pages_1 = [
        create_page_with_mirror(
            region_slug="augsburg",
            name_add=f"-{i}",
        )[0]
        for i in range(num_undeletable_1)
    ]
    undeletable_pages_2 = [
        create_page_with_children(
            region_slug="augsburg",
            root_name_add=f"-{i}",
            num_children=1,
        )
        for i in range(num_undeletable_2)
    ]
    instance_ids: BulkActionIDs = {
        "deletable": deletable_pages,
        "undeletable": [undeletable_pages_1, undeletable_pages_2],
    }
    fail_reason = [
        "you cannot delete a page that is embedded as live content by another page.",
        "you cannot delete a page which has subpages.",
    ]
    url = reverse(
        "bulk_delete_pages",
        kwargs={"region_slug": "augsburg", "language_slug": "en"},
    )
    assert_bulk_delete(
        Page, instance_ids, url, (client, role), caplog, settings, fail_reason
    )
