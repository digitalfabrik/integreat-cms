"""
This module contains custom Django storages
"""

import logging

from django.conf import settings
from django.contrib.messages import constants
from django.contrib.messages.storage.fallback import FallbackStorage
from django.utils.translation import override

logger = logging.getLogger(__name__)

# 25 is not a default logging level, so it has to be added manually
logging.addLevelName(constants.SUCCESS, "SUCCESS")


class MessageLoggerStorage(FallbackStorage):
    """
    Custom messages storage to add debug logging for all messages

    Set the :setting:`django:MESSAGE_STORAGE` setting to the module path of this class to enable logging.
    """

    def add(self, level, message, extra_tags=""):
        """
        Add a mew message

        :param level: The level of the message, see :ref:`message-level-constants`
        :type level: int

        :param message: The message
        :type message: str | ~django.utils.functional.Promise

        :param extra_tags: Additional level tags
        :type extra_tags: str | ~django.utils.functional.Promise
        """
        if settings.MESSAGE_LOGGING_ENABLED:
            # Show logs in English if message was provided as lazy translated string
            with override("en"):
                logger.log(level, message)
        super().add(level, message, extra_tags)
