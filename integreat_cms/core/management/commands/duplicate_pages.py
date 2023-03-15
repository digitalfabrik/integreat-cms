import copy
import logging
import random
import string

from django.core.management.base import CommandError
from django.utils.text import slugify

from ....cms.models import Page, Region
from ..debug_command import DebugCommand

logger = logging.getLogger(__name__)


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
    new_page = (
        new_parent.add_child(instance=new_page)
        if new_parent
        else Page.add_root(instance=new_page)
    )
    # Fix parent field
    new_page = Page.objects.get(id=new_page.id)
    new_page.parent = new_page.get_parent(update=True)
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


class Command(DebugCommand):
    """
    Management command to duplicate all pages of a region
    """

    help = "Duplicate all pages of a specific region"

    def add_arguments(self, parser):
        """
        Define the arguments of this command

        :param parser: The argument parser
        :type parser: ~django.core.management.base.CommandParser
        """
        parser.add_argument("region_slug", help="The slug of the region")

    # pylint: disable=arguments-differ
    def handle(self, *args, region_slug, **options):
        r"""
        Try to run the command

        :param \*args: The supplied arguments
        :type \*args: list

        :param region_slug: The slug of the given region
        :type region_slug: str

        :param \**options: The supplied keyword options
        :type \**options: dict

        :raises ~django.core.management.base.CommandError: When the input is invalid
        """
        try:
            region = Region.objects.get(slug=region_slug)
        except Region.DoesNotExist as e:
            raise CommandError(
                f'Region with slug "{region_slug}" does not exist.'
            ) from e

        logger.info("Duplicating pages for region %s", region)
        duplicate_pages(region)
        self.print_success(f'✔ Successfully duplicated pages for region "{region}".')
