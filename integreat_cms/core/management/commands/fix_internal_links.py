from __future__ import annotations

import logging
import time
from collections import defaultdict
from copy import deepcopy
from functools import partial
from typing import DefaultDict, TYPE_CHECKING
from urllib.parse import unquote

from django.contrib.auth import get_user_model
from django.core.management.base import CommandError
from linkcheck.listeners import tasks_queue
from linkcheck.models import Url
from lxml.html import rewrite_links

from ....cms.models import Region
from ....cms.models.abstract_content_translation import AbstractContentTranslation
from ....cms.utils import internal_link_utils
from ....cms.utils.linkcheck_utils import (
    fix_content_link_encoding,
    get_region_links,
    save_new_version,
)
from ..log_command import LogCommand

if TYPE_CHECKING:
    from typing import Any

    from django.core.management.base import CommandParser

    from ....cms.models import User

logger = logging.getLogger(__name__)


def get_region(region_slug: str) -> Region:
    """
    Get a region object by slug or raise an error if not found

    :param region_slug: Region slug
    :return: Region
    """
    try:
        return Region.objects.get(slug=region_slug)
    except Region.DoesNotExist as e:
        raise CommandError(f'Region with slug "{region_slug}" does not exist.') from e


def get_user(username: str) -> User:
    """
    Get a user by username or raise an error if not found

    :param username: Username
    :return: User
    """
    try:
        return get_user_model().objects.get(username=username)
    except get_user_model().DoesNotExist as e:
        raise CommandError(f'User with username "{username}" does not exist.') from e


class Command(LogCommand):
    """
    Management command to automatically fix broken internal links in the whole content
    Links will be fixed in three cases:
    1. A parent page has been moved, so the slug is identical but the path is not correct anymore
    2. The slug of a page has been changed, so a link might reference an older version of a page
    3. A translation has been created, but the links it contains still point to the source language

    In none of these cases will the link text be changed.
    """

    help = "Search & fix broken internal links in the content"

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Define the arguments of this command

        :param parser: The argument parser
        """
        parser.add_argument(
            "--region-slug", help="Only fix links in the region with this slug"
        )
        parser.add_argument("--username", help="The username of the creator")
        parser.add_argument(
            "--commit",
            action="store_true",
            help="Whether changes should be written to the database",
        )

    # pylint: disable=arguments-differ, too-many-locals
    def handle(
        self, *args: Any, region_slug: str, username: str, commit: bool, **options: Any
    ) -> None:
        r"""
        Try to run the command

        :param \*args: The supplied arguments
        :param region_slug: The slug of the given region
        :param username: The username of the creator
        :param commit: Whether changes should be written to the database
        :param \**options: The supplied keyword options
        :raises ~django.core.management.base.CommandError: When the input is invalid
        """
        self.set_logging_stream()

        region = get_region(region_slug) if region_slug else None
        user = get_user(username) if username else None

        translation_updates: DefaultDict[AbstractContentTranslation, dict[str, str]] = (
            defaultdict(dict)
        )

        query = Url.objects.all()
        if region:
            region_links = get_region_links(region)
            query = Url.objects.filter(links__in=region_links).distinct()

        for url in query:
            if not url.internal:
                continue
            source_translation = internal_link_utils.get_public_translation_for_link(
                url.url
            )
            if not source_translation:
                continue

            for link in url.links.all().prefetch_related("content_object__language"):
                target_language_slug = link.content_object.language.slug
                target_translation = source_translation
                if target_language_slug != source_translation.language.slug:
                    target_translation = (
                        source_translation.foreign_object.get_public_translation(
                            target_language_slug
                        )
                    )

                target_url = target_translation.full_url
                source_url = unquote(url.url)
                if target_url.strip("/") != source_url.strip("/"):
                    logger.debug(
                        "%r: %r -> %r", link.content_object, source_url, target_url
                    )
                    translation_updates[link.content_object][source_url] = target_url

        # Now perform all updates
        for translation, url_updates in translation_updates.items():
            replace_links_of_translation(translation, url_updates, user, commit)

        # Wait until all post-save signals have been processed
        logger.debug("Waiting for linkcheck listeners to update link database...")
        time.sleep(0.1)
        tasks_queue.join()

        if commit:
            logger.success("✔ Successfully finished fixing broken internal links.")  # type: ignore[attr-defined]
        else:
            logger.info("✔ Finished dry-run of fixing broken internal links.")


def replace_links_of_translation(
    translation: AbstractContentTranslation,
    rules: dict[str, str],
    user: Any | None,
    commit: bool,
) -> None:
    """
    Replaces links on a single translation

    :param translation: The translation to modify
    :param rules: The rules how to replace the links. The keys are the old urls and the values are the new urls
    :param user: The user that should be credited for this action
    :param commit: Whether to write to the database
    """
    new_translation = deepcopy(translation)
    new_translation.content = fix_content_link_encoding(
        rewrite_links(new_translation.content, partial(replace_link_helper, rules))
    )
    logger.debug(
        "Replacing %r link(s) in %r: %r", len(rules), new_translation, rules.keys()
    )
    if commit:
        save_new_version(translation, new_translation, user)


def replace_link_helper(rules: dict[str, str], link: str) -> str:
    """
    Helper function to update a link according to the given rules
    :param rules: A dict where the keys are the old urls and the values are the new urls
    :param link: The link to replace according to the rules
    :return: Returns the updated link if a matching rules is found, otherwise returns it unmodified
    """
    return rules.get(link, link)
