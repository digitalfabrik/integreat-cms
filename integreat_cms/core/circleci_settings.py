"""
Django settings for our CircleCI workflow.
All configuration is imported from :mod:`~integreat_cms.core.settings` except it sets all logging to simple console output.
For more information on this file, see :doc:`django:topics/settings`.
For the full list of settings and their values, see :doc:`django:ref/settings`.
"""

# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import
from __future__ import annotations

from .settings import *

#: Set a dummy secret key for CircleCI build even if it's not in debug mode
SECRET_KEY = "dummy"
#: Set dummy key to test push notifications
FCM_KEY = "dummy"
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
#: Use debug logging on CircleCI
LOG_LEVEL = "DEBUG"
#: Disable linkcheck listeners on CircleCI
LINKCHECK_DISABLE_LISTENERS = True
#: Enable logging of all entries from the messages framework
MESSAGE_LOGGING_ENABLED = True
# Disable background tasks during testing
BACKGROUND_TASKS_ENABLED = False
