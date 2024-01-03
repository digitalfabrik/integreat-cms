from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.management.base import CommandError
from django.test.client import AsyncRequestFactory

from ....cms.forms import PageTranslationForm
from ....cms.models import Region, User
from ....summ_ai_api.summ_ai_api_client import SummAiApiClient
from ..log_command import LogCommand

if TYPE_CHECKING:
    from typing import Any

    from django.core.management.base import CommandParser

logger = logging.getLogger(__name__)


def summ_ai_bulk(region: Region, username: str, initial: bool = True) -> None:
    """
    Translate a complete region into Easy German

    :param region: The current region
    :param username: The username of the creator of the translation objects
    :param initial: Whether existing translations should not be updated
    """
    logger.info(
        "Translating %r into Easy German%s",
        region,
        " initially" if initial else "",
    )
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist as e:
        raise CommandError(f'User with username "{username}" does not exist.') from e
    # Fake request object to simulate real usage
    request = AsyncRequestFactory().get(f"/{region.slug}")
    request.session = "session"
    # pylint: disable=protected-access
    request._messages = FallbackStorage(request)
    request.region = region
    request.user = user
    # Initialize client
    api_client = SummAiApiClient(request, PageTranslationForm)
    # Translate all pages
    for page in region.pages.filter(explicitly_archived=False).cache_tree(
        archived=False
    ):
        try:
            if initial and (
                target := page.get_translation(
                    settings.SUMM_AI_EASY_GERMAN_LANGUAGE_SLUG
                )
            ):
                logger.debug("[bot] Translation %r already exists, skipping", target)
                continue
            logger.info("[bot] Translating page %r", page)
            api_client.translate_object(
                page, settings.SUMM_AI_EASY_GERMAN_LANGUAGE_SLUG
            )
            source = page.get_translation(settings.SUMM_AI_GERMAN_LANGUAGE_SLUG)
            if source and source.content.strip():
                time.sleep(30)
        # pylint: disable=broad-exception-caught
        except Exception as e:
            logger.exception(e)
            time.sleep(30)
    logger.info(
        "Successfully translated %r into Easy German",
        region,
    )


class Command(LogCommand):
    """
    Management command to create an initial translation for Easy German via SUMM.AI
    """

    help: str = "Creates an initial translation for Easy German via SUMM.AI"

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Define the arguments of this command

        :param parser: The argument parser
        """
        parser.add_argument("region_slug", help="The slug of the region")
        parser.add_argument("username", help="The username of the creator")
        parser.add_argument(
            "--initial",
            action="store_true",
            help="Whether existing translations should not be updated",
        )

    # pylint: disable=arguments-differ
    def handle(
        self, *args: Any, region_slug: str, username: str, initial: bool, **options: Any
    ) -> None:
        r"""
        Try to run the command

        :param \*args: The supplied arguments
        :param region_slug: The slug of the given region
        :param username: The username of the creator
        :param initial: Whether existing translations should not be updated
        :param \**options: The supplied keyword options
        """
        self.set_logging_stream()

        if not settings.SUMM_AI_ENABLED:
            raise CommandError("SUMM.AI API is disabled globally.")
        try:
            region = Region.objects.get(slug=region_slug)
        except Region.DoesNotExist as e:
            raise CommandError(
                f'Region with slug "{region_slug}" does not exist.'
            ) from e
        if not region.summ_ai_enabled:
            raise CommandError(f'SUMM.AI API is disabled in "{region}".')
        if settings.SUMM_AI_TEST_MODE:
            logger.info(
                "SUMM.AI API is enabled, but in test mode. No credits get charged, but only a dummy text is returned."
            )
        elif settings.DEBUG:
            logger.info(
                "SUMM.AI API is enabled, but in debug mode. Text is really translated and credits get charged, but user is 'testumgebung'"
            )
        summ_ai_bulk(region, username, initial)
        logger.success("Successfully translated region %r into Easy German", region)  # type: ignore[attr-defined]
