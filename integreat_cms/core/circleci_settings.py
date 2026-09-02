"""
Django settings for our CircleCI workflow.
All configuration is imported from :mod:`~integreat_cms.core.test_settings`
and then CI-specific logging is configured for console output.
For more information on this file, see :doc:`django:topics/settings`.
For the full list of settings and their values, see :doc:`django:ref/settings`.
"""

from __future__ import annotations

import sys

from .test_settings import *

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
