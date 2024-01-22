from __future__ import annotations

import copy
import logging
import random
import string
from typing import TYPE_CHECKING

from django.core.management.base import CommandError
from django.utils.text import slugify

from ....cms.models import Page, Region
from ..debug_command import DebugCommand

if TYPE_CHECKING:
    from typing import Any

    from django.core.management.base import CommandParser

logger = logging.getLogger(__name__)


def duplicate_page(old_page: Page, new_parent: Page | None = None) -> Page:
    """
    Duplicate a page and insert it as child of the given new parent

    :param old_page: The old page which should be copied
    :param new_parent: The new parent where the duplicate should reside
    :return: The copied page
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


def duplicate_pages(
    region: Region, old_parent: Page | None = None, new_parent: Page | None = None
) -> None:
    """
    Duplicate pages recursively for the given region

    :param region: The given region
    :param old_parent: The old parent page which descendants should be copied
    :param new_parent: The new parent where the duplicates should reside
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

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Define the arguments of this command

        :param parser: The argument parser
        """
        parser.add_argument("region_slug", help="The slug of the region")

    # pylint: disable=arguments-differ
    def handle(self, *args: Any, region_slug: str, **options: Any) -> None:
        r"""
        Try to run the command

        :param \*args: The supplied arguments
        :param region_slug: The slug of the given region
        :param \**options: The supplied keyword options
        :raises ~django.core.management.base.CommandError: When the input is invalid
        """
        self.set_logging_stream()

        try:
            region = Region.objects.get(slug=region_slug)
        except Region.DoesNotExist as e:
            raise CommandError(
                f'Region with slug "{region_slug}" does not exist.'
            ) from e

        logger.info("Duplicating pages for %r", region)
        duplicate_pages(region)
        logger.success("✔ Successfully duplicated pages for %r.", region)  # type: ignore[attr-defined]
