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
#: Tests must never talk to a real Redis instance: the base settings enable
#: django-redis and cacheops whenever ``INTEGREAT_CMS_REDIS_CACHE`` is set, but
#: cacheops' query-result caching breaks ``django_assert_num_queries``
#: assertions and the autouse ``clear_cache`` fixture would flush the
#: developer's Redis. Force the local-memory backend and uninstall cacheops.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    },
}
if "cacheops" in INSTALLED_APPS:
    INSTALLED_APPS.remove("cacheops")
#: Disable linkcheck listeners during testing
LINKCHECK_DISABLE_LISTENERS = True
#: Disable background tasks during testing
BACKGROUND_TASKS_ENABLED = False
#: Enable logging of all entries from the messages framework
MESSAGE_LOGGING_ENABLED = True
