from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.core.management.base import CommandError

from ....cms.models import Region
from ....cms.utils.linkcheck_utils import replace_links
from ..log_command import LogCommand

if TYPE_CHECKING:
    from typing import Any

    from django.core.management.base import CommandParser

logger = logging.getLogger(__name__)


class Command(LogCommand):
    """
    Management command to replace links in the whole content
    """

    help = "Search & replace links in the content"

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Define the arguments of this command

        :param parser: The argument parser
        """
        parser.add_argument("search", help="The (partial) URL to search")
        parser.add_argument("replace", help="The (partial) URL to replace")
        parser.add_argument(
            "--region-slug", help="Only replace links in the region with this slug"
        )
        parser.add_argument("--username", help="The username of the creator")
        parser.add_argument(
            "--commit",
            action="store_true",
            help="Whether changes should be written to the database",
        )

    # pylint: disable=arguments-differ
    def handle(
        self,
        *args: Any,
        search: str,
        replace: str,
        region_slug: str,
        username: str,
        commit: bool,
        **options: Any,
    ) -> None:
        r"""
        Try to run the command

        :param \*args: The supplied arguments
        :param search: The (partial) URL to search
        :param replace: The (partial) URL to replace
        :param region_slug: The slug of the given region
        :param username: The username of the creator
        :param commit: Whether changes should be written to the database
        :param \**options: The supplied keyword options
        :raises ~django.core.management.base.CommandError: When the input is invalid
        """
        self.set_logging_stream()

        if region_slug:
            try:
                region = Region.objects.get(slug=region_slug)
            except Region.DoesNotExist as e:
                raise CommandError(
                    f'Region with slug "{region_slug}" does not exist.'
                ) from e
        else:
            region = None
        if username:
            try:
                user = get_user_model().objects.get(username=username)
            except get_user_model().DoesNotExist as e:
                raise CommandError(
                    f'User with username "{username}" does not exist.'
                ) from e
        else:
            user = None

        replace_links(search, replace, region=region, user=user, commit=commit)

        if commit:
            logger.success(  # type: ignore[attr-defined]
                "✔ Successfully replaced %r with %r in content links.",
                search,
                replace,
            )
        else:
            logger.info(
                "✔ Finished dry-run of replacing %r with %r in content links.",
                search,
                replace,
            )
