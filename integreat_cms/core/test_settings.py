"""
Django settings for running tests.

Shared by both local test runs (``tools/test.sh``) and CI (CircleCI).
All configuration is imported from :mod:`~integreat_cms.core.settings`
and then overridden with test-specific values.

For more information on this file, see :doc:`django:topics/settings`.
For the full list of settings and their values, see :doc:`django:ref/settings`.
"""

from __future__ import annotations

from .settings import *

#: Set a dummy secret key for test environments
SECRET_KEY = "dummy"  # noqa: S105
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
#: Set dummy Google Translate credential path
GOOGLE_APPLICATION_CREDENTIALS = "dummy"
#: Set dummy Google project ID
GOOGLE_PROJECT_ID = "dummy"
#: Enable manually because existing setting derives from the unset env var
GOOGLE_TRANSLATE_ENABLED = True
#: Disable linkcheck listeners during testing
LINKCHECK_DISABLE_LISTENERS = True
#: Disable background tasks during testing
BACKGROUND_TASKS_ENABLED = False
#: Enable logging of all entries from the messages framework
MESSAGE_LOGGING_ENABLED = True
