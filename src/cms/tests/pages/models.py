"""
This is a collection of unit tests for the page and page translation model.
"""

from django.test import TestCase
from cms.models import Page, PageTranslation, Region


class PageTest(TestCase):
    """
    Unit test for the Page model
    """

    def setUp(self):
        """
        Setup run to create a region and page objects.
        """
        self.region = Region.objects.create(
            aliases=[], push_notification_channels=[], slug="testregion"
        )
        self.page1 = Page.objects.create(region=self.region)
        self.page2 = Page.objects.create(parent=self.page1, region=self.region)
        self.page3 = Page.objects.create(parent=self.page2, region=self.region)

    def test_depth_no_parent(self):
        """
        Depth is correctly determined for page on first level.
        """
        self.assertTrue(self.page1.depth == 0)

    def test_depth_third_level(self):
        """
        Depth is correctly determined for page on third level.
        """
        self.assertTrue(self.page3.depth == 2)

    def test_get_archived(self):
        """
        The function ``get_archived()`` returns the correct number of pages.
        """
        self.page1.archived = True
        self.page1.save()
        self.page2.archived = True
        self.page2.save()
        archived = Page.get_archived(self.region.slug)
        self.assertTrue(len(archived) == 2)


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
