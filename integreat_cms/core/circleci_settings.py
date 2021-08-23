"""
Django settings for our CircleCI workflow.
All configuration is imported from :mod:`~integreat_cms.core.settings` except it sets all logging to simple console output.
For more information on this file, see :doc:`topics/settings`.
For the full list of settings and their values, see :doc:`ref/settings`.
"""
# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import
from .settings import *


#: Set a dummy secret key for CircleCI build even if it's not in debug mode
SECRET_KEY = "dummy"

# Use simple non-colored logging in circleci
for logger in LOGGING["loggers"].values():
    logger["handlers"] = ["console"]
