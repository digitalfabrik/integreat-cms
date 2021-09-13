"""
Django settings for our CircleCI workflow.
All configuration is imported from :mod:`backend.settings` except it sets all logging to simple console output.
For more information on this file, see :doc:`topics/settings`.
For the full list of settings and their values, see :doc:`ref/settings`.
"""
# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import
from .settings import *


# Use simple non-colored logging in circleci
for logger in LOGGING["loggers"].values():
    logger["handlers"] = ["console"]
