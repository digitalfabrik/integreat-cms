"""
Test repair tree util
"""

import pytest

from integreat_cms.cms.models import Page, Region
from integreat_cms.cms.utils.repair_tree import repair_tree


# pylint: disable=too-few-public-methods
class TestRepairTree:
    """
    Test whether to_ical_rrule_string function is calculating the rrule correctly
    """

    @pytest.mark.django_db
    def test_repair_tree(self, load_test_data: None) -> None:
        region = Region.objects.get(slug="augsburg")

        # "created_date", "lft", "rgt", "tree_id", "depth", "parent_id", "region_id", "explicitly_archi..., "api_token", "hix_ignore"
        root_page = Page(region=region, lft=2, rgt=6, tree_id=999, depth=0)
        child1_page = Page(region=region, lft=1, rgt=4, tree_id=999, depth=1, parent=root_page)
        child2_page = Page(region=region, lft=4, rgt=5, tree_id=999, depth=1, parent=root_page)

        root_page.save()
        child1_page.save()
        child2_page.save()

        # Reload from database and ensure that there is no new fix method hooked into .save()
        # that could make this test give a false positive
        root_page = Page.objects.get(pk=root_page.pk)
        child1_page = Page.objects.get(pk=child1_page.pk)
        child2_page = Page.objects.get(pk=child2_page.pk)

        assert root_page.lft == 2 # intentional mistake, should be 1
        assert root_page.rgt == 6
        assert child1_page.lft == 1 # intentional mistake, should be 2
        assert child1_page.rgt == 4 # intentional mistake, should be 3
        assert child2_page.lft == 4
        assert child2_page.rgt == 5

        repair_tree(page_id=root_page.pk, commit=True)

        # We have to reload the objects from the database
        root_page = Page.objects.get(pk=root_page.pk)
        child1_page = Page.objects.get(pk=child1_page.pk)
        child2_page = Page.objects.get(pk=child2_page.pk)

        assert root_page.lft == 1
        assert root_page.rgt == 6
        assert child1_page.lft == 2
        assert child1_page.rgt == 3
        assert child2_page.lft == 4
        assert child2_page.rgt == 5

        child2_page.delete()
        child1_page.delete()
        root_page.delete()
