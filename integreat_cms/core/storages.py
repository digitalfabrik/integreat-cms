"""
This module contains custom Django storages
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.messages.storage.fallback import FallbackStorage
from django.utils.translation import override

if TYPE_CHECKING:
    from django.utils.functional import Promise

logger = logging.getLogger(__name__)


class MessageLoggerStorage(FallbackStorage):
    """
    Custom messages storage to add debug logging for all messages

    Set the :setting:`django:MESSAGE_STORAGE` setting to the module path of this class to enable logging.
    """

    def add(self, level: int, message: str | Promise, extra_tags: str = "") -> None:
        """
        Add a mew message

        :param level: The level of the message, see :ref:`message-level-constants`
        :param message: The message
        :param extra_tags: Additional level tags
        """
        if settings.MESSAGE_LOGGING_ENABLED:
            # Show logs in English if message was provided as lazy translated string
            with override("en"):
                logger.log(level, message)
        super().add(level, message, extra_tags)
