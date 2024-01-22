from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from urllib.parse import unquote

from django.contrib.auth import get_user_model
from django.core.management.base import CommandError
from linkcheck.models import Url

from ....cms.models import Region
from ....cms.utils import internal_link_utils
from ....cms.utils.linkcheck_utils import replace_links
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

    # pylint: disable=arguments-differ
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

        for url in Url.objects.all():
            if not url.internal:
                continue
            source_translation = internal_link_utils.get_public_translation_for_link(
                url.url
            )
            if not source_translation:
                continue

            for link in url.links.all():
                target_language_slug = link.content_object.language.slug
                if target_translation := source_translation.foreign_object.get_public_translation(
                    target_language_slug
                ):
                    target_url = target_translation.full_url
                    source_url = unquote(url.url)
                    if target_url.strip("/") != source_url.strip("/"):
                        replace_links(
                            source_url,
                            target_url,
                            region=region,
                            partial_match=False,
                            language=target_translation.language,
                            user=user,
                            commit=commit,
                        )

        if commit:
            logger.success("✔ Successfully finished fixing broken internal links.")  # type: ignore[attr-defined]
        else:
            logger.info("✔ Finished dry-run of fixing broken internal links.")
