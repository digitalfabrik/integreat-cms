from __future__ import annotations

import logging
import time
from html import unescape
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.core.management.base import CommandError
from linkcheck.listeners import tasks_queue
from linkcheck.models import Url
from lxml.etree import ParserError
from lxml.html import fromstring, tostring

if TYPE_CHECKING:
    from typing import Any

    from django.core.management.base import CommandParser

    from .users.user import User


from ..log_command import LogCommand

logger = logging.getLogger(__name__)


def get_url(url: str) -> Url:
    """
    Get an URL object by url or raise an error if not found

    :param url: url as string
    :return: URL
    """
    try:
        return Url.objects.get(url=url)
    except Url.DoesNotExist as e:
        raise CommandError(f'URL object with url "{url}" does not exist.') from e


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
    Management command to update the link text of ALL links with the given URL.
    ALL links receive the SAME new link text.
    This applies in ALL regions.
    """

    help = "Update link text of the URL"

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Define the arguments of this command

        :param parser: The argument parser
        """
        parser.add_argument(
            "--target-url",
            required=True,
            help="The URL whose link text needs to be changed",
        )
        parser.add_argument("--new-link-text", required=True, help="The new link text")
        parser.add_argument("--username", help="The username of the creator")

    def handle(
        self,
        *args: Any,
        target_url: str,
        new_link_text: str,
        username: str,
        **options: Any,
    ) -> None:
        r"""
        Try to run the command

        :param \*args: The supplied arguments
        :param target_url: URL whose link texts need to be updated
        :param new_link_text: New link text to replace with the current link texts
        :param username: The username of the creator
        :param \**options: The supplied keyword options
        :raises ~django.core.management.base.CommandError: When the input is invalid
        """
        self.set_logging_stream()

        target_url_object = get_url(target_url)
        user = get_user(username) if username else None

        target_links = target_url_object.links.all()

        target_contents = {target_link.content_object for target_link in target_links}

        for target_content in target_contents:
            if target_content._meta.default_related_name in [
                "page_translations",
                "event_translations",
                "poi_translations",
                "imprint_translations",
            ]:
                try:
                    content = fromstring(target_content.content)
                except ParserError:
                    logger.info(
                        "A link text in %r could not be updated automatically.",
                        target_content,
                    )

                for elem, _, link, _ in content.iterlinks():
                    if link == target_url:
                        elem.text = new_link_text

                new_translation = target_content.create_new_version_copy(user)
                new_translation.content = unescape(
                    tostring(content, encoding="unicode", with_tail=False)
                )

                if new_translation.content != target_content.content:
                    target_content.links.all().delete()
                    new_translation.save()
        # Wait until all post-save signals have been processed
        time.sleep(0.1)
        # Wait until all background tasks of linkcheck indexing the new content objects have been processed
        tasks_queue.join()

        logger.success("✔ Successfully finished updating link texts.")  # type: ignore[attr-defined]
