"""
This is a collection of unit tests for the page and page translation model.
"""

from django.test import TestCase
from ...models import Page, PageTranslation, Region


class PageTest(TestCase):
    """
    Unit test for the Page model
    """

    def setUp(self):
        """
        Setup run to create a region and page objects.
        """
        self.region = Region.objects.create(aliases=[], slug="testregion")
        self.page1 = Page.add_root(region=self.region)
        self.page2 = self.page1.add_child(parent=self.page1, region=self.region)
        self.page3 = self.page2.add_child(parent=self.page2, region=self.region)

    def test_depth_no_parent(self):
        """
        Depth is correctly determined for page on first level.
        """
        self.assertTrue(self.page1.depth == 1)

    def test_depth_third_level(self):
        """
        Depth is correctly determined for page on third level.
        """
        self.assertTrue(self.page3.depth == 3)


class PageTranslationTest(TestCase):
    """
    Unit test for the page translation model
    """

    def setUp(self):
        """
        Setup run to create a region and page translation object.
        """
        self.region = Region.objects.create(
            aliases=[], push_notification_channels=[], slug="testregion"
        )
        self.pageTranslation = PageTranslation.objects.create()
