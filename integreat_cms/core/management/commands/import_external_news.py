from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.core.management.base import BaseCommand

from ....news_managers import registry

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Management command to import news items from the external sources
    """

    help = "Get news items from the external sources"

    def handle(self, *args: Any, **options: Any) -> None:
        r"""
        Imports posts from the external news sources and save in the cache

        :param \*args: The supplied arguments
        :param \**options: The supplied keyword options
        """
        for news_manager in registry.CHOICES:
            news_manager.import_news_items()
