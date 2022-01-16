"""
Please run this script via the dev tool duplicate_pages.sh to make sure all environment
variables are passed correctly and Django can be set up.
"""
import copy
import logging
import random
import string
import sys

from django.utils.text import slugify

logger = logging.getLogger(__name__)

if __name__ != "django.core.management.commands.shell":
    logger.error("Please run this script via the dev tool duplicate_pages.sh")
    sys.exit()

# pylint: disable=wrong-import-position
from integreat_cms.cms.models import Region, Page


def duplicate_page(old_page, new_parent=None):
    """
    Duplicate a page and insert it as child of the given new parent

    :param old_page: The old page which should be copied
    :type old_page: ~integreat_cms.cms.models.pages.page.Page

    :param new_parent: The new parent where the duplicate should reside
    :type new_parent: ~integreat_cms.cms.models.pages.page.Page

    :return: The copied page
    :rtype: ~integreat_cms.cms.models.pages.page.Page
    """
    if new_parent:
        # Re-query from database to update tree structure
        new_parent = Page.objects.get(id=new_parent.id)
    logger.debug("Duplicating page %r with new parent %r", old_page, new_parent)
    translations = old_page.translations.all()
    logger.debug("Old translations: %r", translations)
    new_page = copy.deepcopy(old_page)
    new_page.id = None
    # pylint: disable=protected-access
    new_page._state.adding = True
    if new_parent:
        new_page = new_parent.add_child(instance=new_page)
    else:
        new_page = Page.add_root(instance=new_page)
    # Fix parent field
    new_page = Page.objects.get(id=new_page.id)
    new_page.save()
    for translation in translations:
        rand_str = "".join(random.choices(string.printable, k=5))
        new_title = translation.title.split(" - ")[0] + f" - {rand_str}"
        translation.id = None
        translation.page = new_page
        translation.title = new_title
        translation.slug = slugify(new_title)
        translation.save()
    logger.debug("New translations: %r", new_page.translations.all())
    return new_page


def duplicate_pages(region, old_parent=None, new_parent=None):
    """
    Duplicate pages recursively for the given region

    :param region: The given region
    :type region: ~integreat_cms.cms.models.regions.region.Region

    :param old_parent: The old parent page which descendants should be copied
    :type old_parent: ~integreat_cms.cms.models.pages.page.Page

    :param new_parent: The new parent where the duplicates should reside
    :type new_parent: ~integreat_cms.cms.models.pages.page.Page
    """
    logger.info(
        "Duplicating pages for old parent %r and new parent %r",
        old_parent,
        new_parent,
    )
    for old_page in region.pages.filter(parent=old_parent):
        new_page = duplicate_page(old_page, new_parent=new_parent)
        duplicate_pages(region, old_parent=old_page, new_parent=new_page)


selected_region = Region.objects.first()
logger.info("Duplicating pages for region %r", selected_region)
duplicate_pages(selected_region)
