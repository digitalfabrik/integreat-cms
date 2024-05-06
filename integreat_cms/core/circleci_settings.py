"""
Django settings for our CircleCI workflow.
All configuration is imported from :mod:`~integreat_cms.core.settings` except it sets all logging to simple console output.
For more information on this file, see :doc:`django:topics/settings`.
For the full list of settings and their values, see :doc:`django:ref/settings`.
"""

# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import
from __future__ import annotations

import sys

from .settings import *

#: Set a dummy secret key for CircleCI build even if it's not in debug mode
SECRET_KEY = "dummy"
#: Set dummy credentials path to test push notifications
FCM_CREDENTIALS = "dummy"
#: Enable manually because existing setting derives from the unset env var
FCM_ENABLED = True
#: Set dummy SUMM.AI API key to test translations into Easy German
SUMM_AI_API_KEY = "dummy"
#: Enable manually because existing setting derives from the unset env var
SUMM_AI_ENABLED = True
#: Set dummy DeepL key to test automatic translations via DeepL API
DEEPL_AUTH_KEY = "dummy"
#: Enable manually because existing setting derives from the unset env var
DEEPL_ENABLED = True
#: Set dummy Textlab key to test automatic translations via Textlab API
TEXTLAB_API_KEY = "dummy"
#: Enable manually because existing setting derives from the unset env var
TEXTLAB_API_ENABLED = True
#: Disable linkcheck listeners on CircleCI
LINKCHECK_DISABLE_LISTENERS = True
# Disable background tasks during testing
BACKGROUND_TASKS_ENABLED = False
#: Enable logging of all entries from the messages framework
MESSAGE_LOGGING_ENABLED = True
#: Use debug logging on CircleCI
LOG_LEVEL = "DEBUG"
#: Logging configuration dictionary (see :setting:`django:LOGGING`)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "management-command": {
            "()": ColorFormatter,
            "format": "{message}",
            "style": "{",
        },
        "logfile": {
            "()": RequestFormatter,
            "format": "{asctime} {levelname:7} {name} - {message}",
            "datefmt": "%b %d %H:%M:%S",
            "style": "{",
        },
    },
    "filters": {
        "only_stdout": {
            "()": "django.utils.log.CallbackFilter",
            "callback": lambda record: record.levelno <= SUCCESS,
        },
    },
    "handlers": {
        # Send DEBUG, INFO and SUCCESS to stdout
        "management-command-stdout": {
            "class": "logging.StreamHandler",
            "filters": ["only_stdout"],
            "formatter": "management-command",
            "level": "DEBUG",
            "stream": sys.stdout,
        },
        # Send WARNING, ERROR and CRITICAL to stderr
        "management-command-stderr": {
            "class": "logging.StreamHandler",
            "formatter": "management-command",
            "level": "WARNING",
        },
        "logfile": {
            "class": "logging.FileHandler",
            "filename": LOGFILE,
            "formatter": "logfile",
        },
    },
    "loggers": {
        "integreat_cms": {
            "handlers": ["logfile"],
            "level": LOG_LEVEL,
        },
        "integreat_cms.core.management.commands": {
            "handlers": [
                "management-command-stdout",
                "management-command-stderr",
                "logfile",
            ],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "auth": {
            "handlers": ["logfile"],
            "level": "INFO",
        },
    },
}
