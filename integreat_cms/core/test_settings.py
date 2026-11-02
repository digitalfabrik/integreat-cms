"""
Django settings for running tests.

Shared by both local test runs (``tools/test.py``) and CI (CircleCI).
All configuration is imported from :mod:`~integreat_cms.core.settings`
and then overridden with test-specific values.

For more information on this file, see :doc:`django:topics/settings`.
For the full list of settings and their values, see :doc:`django:ref/settings`.
"""

from __future__ import annotations

from .settings import *

#: Set a dummy secret key for CircleCI build even if it's not in debug mode
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
#: The app code calls cacheops' ``invalidate_obj``/``invalidate_model`` directly,
#: which contact Redis regardless of the app being installed — with no Redis
#: reachable, redis-py's connection retries add minutes of backoff sleeps to
#: every tree operation. This flag makes all cacheops entry points no-ops.
CACHEOPS_ENABLED = False
#: Disable linkcheck listeners on CircleCI
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
#: The app code calls cacheops' ``invalidate_obj``/``invalidate_model`` directly,
#: which contact Redis regardless of the app being installed — with no Redis
#: reachable, redis-py's connection retries add minutes of backoff sleeps to
#: every tree operation. This flag makes all cacheops entry points no-ops.
CACHEOPS_ENABLED = False
#: Disable linkcheck listeners during testing
LINKCHECK_DISABLE_LISTENERS = True
# Disable background tasks during testing
BACKGROUND_TASKS_ENABLED = False
# Disable auto re-import of external news on demand
EXTERNALNEWS_DISABLE_AUTO_REIMPORT = True
#: Enable logging of all entries from the messages framework
MESSAGE_LOGGING_ENABLED = True

#: Detect N+1 queries with django-zeal (see :doc:`testing`). The autouse ``zeal``
#: fixture in ``tests/conftest.py`` enables detection for every test, the
#: middleware gives each request its own context, so that repeated requests in
#: one test are not mistaken for an N+1.
INSTALLED_APPS.append("zeal")
MIDDLEWARE.insert(0, "zeal.middleware.zeal_middleware")
#: Fail the test on a detected N+1
ZEAL_RAISE = True
#: Executions of the same lazy load from one line to count as N+1 (matches the query report)
ZEAL_NPLUSONE_THRESHOLD = 5
#: Known N+1s which are not fixed yet, each with an example of where it happens.
#: Remove an entry once it is fixed. Only add entries for N+1s which cannot be fixed
#: (e.g. in third-party code) - prefer ``select_related``/``prefetch_related``.
ZEAL_ALLOWLIST: list[dict[str, str]] = [
    # e.g. integreat_cms/cms/models/users/user.py:138
    {"model": "auth.Group", "field": "role"},
    # e.g. integreat_cms/cms/views/roles/role_form_view.py:52
    {"model": "auth.Permission", "field": "content_type"},
    # e.g. integreat_cms/cms/models/abstract_content_model.py:634
    {"model": "cms.Event", "field": "region"},
    # e.g. integreat_cms/cms/models/abstract_content_model.py:263
    {"model": "cms.Event", "field": "translations"},
    # e.g. integreat_cms/cms/models/events/event_translation.py:58
    {"model": "cms.EventTranslation", "field": "event"},
    # e.g. integreat_cms/cms/models/abstract_content_model.py:210
    {"model": "cms.EventTranslation", "field": "language"},
    # e.g. integreat_cms/cms/utils/link_ignore_preservation.py:70
    {"model": "cms.EventTranslation", "field": "links"},
    # e.g. (logging of) __init__.py:400
    {"model": "cms.ExternalCalendar", "field": "events"},
    # e.g. integreat_cms/cms/utils/external_calendar_utils.py:480
    {"model": "cms.ExternalCalendar", "field": "get()"},
    # e.g. integreat_cms/cms/views/feedback/region_feedback_actions.py:219
    {"model": "cms.Feedback", "field": "language"},
    # e.g. integreat_cms/cms/views/feedback/region_feedback_actions.py:219
    {"model": "cms.Feedback", "field": "read_by"},
    # e.g. integreat_cms/cms/models/feedback/region_feedback.py:27
    {"model": "cms.Feedback", "field": "region"},
    # e.g. integreat_cms/cms/views/place_categories/place_category_form_view.py:130
    {"model": "cms.Language", "field": "get()"},
    # e.g. integreat_cms/cms/forms/regions/region_form.py:1033
    {"model": "cms.LanguageTreeNode", "field": "language"},
    # e.g. integreat_cms/core/middleware/timezone_middleware.py:39
    {"model": "cms.LanguageTreeNode", "field": "region"},
    # e.g. integreat_cms/cms/rules.py:58
    {"model": "cms.Page", "field": "editors"},
    # e.g. integreat_cms/cms/forms/regions/region_form.py:986
    {"model": "cms.Page", "field": "embedded_offers"},
    # e.g. integreat_cms/core/management/commands/duplicate_pages.py:43
    {"model": "cms.Page", "field": "get()"},
    # e.g. integreat_cms/cms/models/abstract_content_translation.py:312
    {"model": "cms.Page", "field": "region"},
    # e.g. integreat_cms/cms/models/abstract_content_model.py:263
    {"model": "cms.Page", "field": "translations"},
    # e.g. integreat_cms/cms/models/pages/page_translation.py:428
    {"model": "cms.PageTranslation", "field": "language"},
    # e.g. integreat_cms/cms/views/language_tree/language_tree_node_form_view.py:92
    {"model": "cms.PageTranslation", "field": "links"},
    # e.g. integreat_cms/cms/models/pages/abstract_base_page_translation.py:56
    {"model": "cms.PageTranslation", "field": "page"},
    # e.g. tests/cms/views/contacts/test_contact_form.py:354
    {"model": "cms.Place", "field": "get()"},
    # e.g. integreat_cms/cms/models/contact/contact.py:472
    {"model": "cms.Place", "field": "region"},
    # e.g. integreat_cms/cms/models/abstract_content_model.py:263
    {"model": "cms.Place", "field": "translations"},
    # e.g. integreat_cms/cms/models/place_categories/place_category.py:64
    {"model": "cms.PlaceCategoryTranslation", "field": "language"},
    # e.g. integreat_cms/cms/models/abstract_content_model.py:210
    {"model": "cms.PlaceTranslation", "field": "language"},
    # e.g. integreat_cms/cms/models/places/place_translation.py:71
    {"model": "cms.PlaceTranslation", "field": "place"},
    # e.g. integreat_cms/cms/models/push_notifications/push_notification.py:188
    {"model": "cms.PushNotification", "field": "regions"},
    # e.g. integreat_cms/cms/templatetags/push_notification_filters.py:30
    {"model": "cms.PushNotification", "field": "translations"},
    # e.g. integreat_cms/cms/models/events/recurrence_rule.py:221
    {"model": "cms.RecurrenceRule", "field": "event"},
    # e.g. integreat_cms/cms/models/regions/region.py:921
    {"model": "cms.Region", "field": "imprints"},
    # e.g. tests/cms/views/contacts/test_contact_form.py:347
    {"model": "cms.User", "field": "get()"},
    # e.g. integreat_cms/cms/models/users/user.py:136
    {"model": "cms.User", "field": "groups"},
    # e.g. integreat_cms/cms/models/feedback/feedback.py:43
    {"model": "contenttypes.ContentType", "field": "get()"},
    # e.g. integreat_cms/core/middleware/timezone_middleware.py:39
    {"model": "linkcheck.Link", "field": "content_object"},
    # e.g. tests/cms/models/media/test_media_file.py:239
    {"model": "linkcheck.Link", "field": "get()"},
    # e.g. integreat_cms/cms/models/abstract_content_translation.py:680
    {"model": "linkcheck.Link", "field": "url"},
    # e.g. tests/cms/models/media/test_media_file.py:239
    {"model": "linkcheck.Url", "field": "get()"},
    # e.g. integreat_cms/core/management/commands/fix_internal_links.py:150
    {"model": "linkcheck.Url", "field": "links"},
]
