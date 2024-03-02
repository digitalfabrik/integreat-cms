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
    def test_repair_tree(self) -> None:
        region = Region.objects.get(slug="augsburg")
        root_page = Page(region=region)
        child1_page = Page(region=region, parent=root_page)
        child2_page = Page(region=region, parent=root_page)
        root_page.save()
        child1_page.save()
        child2_page.save()
        child1_page.rgt = 4
        child1_page.save()
        repair_tree(page_id=root_page.pk, commit=True)
        assert root_page.lft == 1
        assert root_page.rgt == 6
        assert child1_page.lft == 2
        assert child1_page.rgt == 3
        assert child2_page.lft == 4
        assert child2_page.rgt == 5
        child2_page.delete()
        child1_page.delete()
        root_page.delete()
