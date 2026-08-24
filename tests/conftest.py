"""
This module contains shared fixtures for pytest
"""

from __future__ import annotations

import datetime
import itertools
import os
from typing import TYPE_CHECKING
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest  # isort: skip — must precede local imports for fixture registration
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.test.client import Client
from linkcheck.listeners import unregister_listeners

from integreat_cms.cms.constants.administrative_division import MUNICIPALITY
from integreat_cms.cms.constants.region_status import ACTIVE
from integreat_cms.cms.constants.status import PUBLIC
from integreat_cms.cms.models import (
    Event,
    EventTranslation,
    Language,
    LanguageTreeNode,
    Page,
    PageTranslation,
    RecurrenceRule,
    Region,
    User,
)
from integreat_cms.core.utils.strtobool import strtobool
from integreat_cms.firebase_api.firebase_security_service import FirebaseSecurityService
from tests.constants import (  # noqa: F401 — re-exported for backward compatibility
    ALL_ROLES,
    ANONYMOUS,
    AUTHOR,
    CMS_TEAM,
    EDITOR,
    HIGH_PRIV_STAFF_ROLES,
    MANAGEMENT,
    OBSERVER,
    PRIV_STAFF_ROLES,
    REGION_ROLES,
    ROLES,
    ROOT,
    SERVICE_TEAM,
    STAFF_ROLES,
    WRITE_ROLES,
)
from tests.mock import MockServer

if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from typing import Any, Final

    from _pytest.fixtures import SubRequest
    from pytest_django.fixtures import SettingsWrapper
    from pytest_django.plugin import _DatabaseBlocker  # type: ignore[attr-defined]
    from pytest_httpserver.httpserver import HTTPServer


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register custom CLI options."""
    parser.addoption(
        "--update-snapshots",
        action="store_true",
        default=False,
        help="Update API expected-output snapshot files instead of asserting against them.",
    )


@pytest.fixture(scope="session")
def update_snapshots(request: pytest.FixtureRequest) -> bool:
    """Whether ``--update-snapshots`` was passed on the CLI."""
    return bool(request.config.getoption("--update-snapshots"))


#: Representative subset covering all permission boundaries (for faster local runs)
QUICK_ROLE_SET: Final = [ROOT, MANAGEMENT, AUTHOR, ANONYMOUS]
#: The roles used for parametrized tests — set QUICK_ROLES=1 to use the subset
TEST_ROLES: Final = (
    QUICK_ROLE_SET if strtobool(os.environ.get("QUICK_ROLES") or "False") else ALL_ROLES
)


@pytest.fixture(scope="session")
def load_test_data(django_db_setup: None, django_db_blocker: _DatabaseBlocker) -> None:
    """
    Load the test data initially for all test cases.

    :param django_db_setup: The fixture providing the database availability
    :param django_db_blocker: The fixture providing the database blocker
    """
    with django_db_blocker.unblock():
        call_command("loaddata", "integreat_cms/cms/fixtures/test_data.json")


@pytest.fixture(scope="function")
def load_test_data_transactional(
    transactional_db: None,
    django_db_blocker: _DatabaseBlocker,
) -> None:
    """
    Load test data for transactional test cases.
    Transactional tests flush the database after each test, so fixtures must be
    reloaded per function. pytest-django ensures these run after all
    non-transactional tests within the same worker.

    :param transactional_db: The fixture providing transaction support for the database
    :param django_db_blocker: The fixture providing the database blocker
    """
    with django_db_blocker.unblock():
        call_command("loaddata", "integreat_cms/cms/fixtures/test_roles.json")
        call_command("loaddata", "integreat_cms/cms/fixtures/test_data.json")


@pytest.fixture(scope="session", params=TEST_ROLES)
def login_role_user(
    request: SubRequest,
    load_test_data: None,
    django_db_blocker: _DatabaseBlocker,
) -> tuple[Client, str]:
    """
    Get the test user of the current role and force a login. Gets executed only once per user.

    :param request: The request object providing the parametrized role variable through ``request.param``
    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param django_db_blocker: The fixture providing the database blocker
    :return: The http client and the current role
    """
    client = Client()
    # Only log in user if the role is not anonymous
    if request.param != ANONYMOUS:
        with django_db_blocker.unblock():
            user = get_user_model().objects.get(username=request.param.lower())
            client.force_login(user)
    return client, request.param


@pytest.fixture(scope="function")
def mock_server(httpserver: HTTPServer) -> MockServer:
    return MockServer(httpserver)


@pytest.fixture(scope="function")
def mock_firebase_credentials() -> Generator[None]:
    patch_obj = patch.object(
        FirebaseSecurityService,
        "_get_access_token",
        return_value="secret access token",
    )
    patch_obj.start()

    yield

    patch_obj.stop()


@pytest.fixture
def clean_news_cache(load_test_data: None) -> Generator[None]:
    """
    Clear external news-source cache entries before and after a test.

    Language slugs are read from the DB so adding or removing a language is
    automatically reflected.
    """
    keys = [
        f"tunews:{slug}" for slug in Language.objects.values_list("slug", flat=True)
    ] + [f"amalnews:{slug}" for slug in Language.objects.values_list("slug", flat=True)]
    for key in keys:
        cache.delete(key)
    yield
    for key in keys:
        cache.delete(key)


@pytest.fixture(autouse=True)
def configure_celery_for_tests(settings: SettingsWrapper) -> None:
    # by default, no worker is running to consume tasks during tests,
    # so we set celery to run synchronously and propagate errors to the test runner
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True


@pytest.fixture(autouse=True)
def clear_leaked_messages(request: SubRequest) -> Generator[None]:
    """
    Discard unread messages from the shared client after every test.

    :meth:`~tests.conftest.login_role_user` is session-scoped, so one client —
    and one cookie jar — is reused for the whole run, while
    :setting:`django:MESSAGE_STORAGE` keeps messages in a cookie. A test that
    triggers a view emitting a message without ever rendering the redirect
    target leaves that message queued in the cookie, where an arbitrary later
    test renders it into its own response and trips content assertions.
    """
    yield
    if "login_role_user" in request.fixturenames:
        client, _role = request.getfixturevalue("login_role_user")
        client.cookies.pop("messages", None)


@pytest.fixture(autouse=True)
def reset_linkcheck_listeners() -> Generator[None]:
    """
    Restore the configured linkcheck listener state around every test.

    :func:`linkcheck.listeners.disable_listeners` re-registers the listeners
    when its context manager exits instead of restoring whatever state was
    active before, so production code paths that use it — the region form,
    :mod:`~integreat_cms.cms.views.regions.region_actions` and
    :mod:`~integreat_cms.cms.views.language_tree.language_tree_actions` —
    leave the listeners connected for the remainder of the worker process,
    even though :setting:`LINKCHECK_DISABLE_LISTENERS` is enabled in
    :mod:`~integreat_cms.core.test_settings`. Any later test that saves
    content then silently gets ``Url``/``Link`` rows it never asked for, which
    makes linkcheck assertions depend on which tests happened to share the
    worker.
    """
    if settings.LINKCHECK_DISABLE_LISTENERS:
        unregister_listeners()
    yield
    if settings.LINKCHECK_DISABLE_LISTENERS:
        unregister_listeners()


@pytest.fixture(autouse=True)
def clear_cache() -> None:
    """
    Reset the cache before every test so cache state cannot leak between tests.

    The cache backend used in tests (:class:`~django.core.cache.backends.locmem.LocMemCache`)
    lives for the lifetime of the worker process, and Django only rolls back the
    database between tests — not the cache. Without this, process-level cache
    state (most notably the API rate-limit counters in
    :func:`~integreat_cms.api.decorators.rate_limited`) accumulates across tests
    and makes assertions depend on test execution order.
    """
    cache.clear()


@pytest.fixture()
def disable_auto_news_reimport(settings: SettingsWrapper) -> None:
    """
    Disable re-import of external news on demand to avoid hitting the real APIs and getting real news posts
    """
    settings.EXTERNALNEWS_DISABLE_AUTO_REIMPORT = True


@pytest.fixture()
def create_language() -> Callable[..., Language]:
    """
    Factory fixture to create a
    :class:`~integreat_cms.cms.models.languages.language.Language` with sensible
    defaults for all required fields, so tests only need to pass the values they
    care about.

    :return: A callable that creates a language
    """
    counter = itertools.count(1)

    def _create_language(slug: str | None = None, **overrides: Any) -> Language:
        n = next(counter)
        defaults: dict[str, Any] = {
            "slug": slug or f"tl{n}",
            "bcp47_tag": f"tl-T{n}",
            "native_name": f"Test Language {n}",
            "english_name": f"Test Language {n}",
            "primary_country_code": "de",
            "table_of_contents": "Inhaltsverzeichnis",
        }
        defaults.update(overrides)
        return Language.objects.create(**defaults)

    return _create_language


@pytest.fixture()
def create_region(
    create_language: Callable[..., Language],
) -> Callable[..., Region]:
    """
    Factory fixture to create a
    :class:`~integreat_cms.cms.models.regions.region.Region` with sensible
    defaults for all required fields.
    If no language tree exists for the region after creation, a default language
    is created and attached automatically.

    :return: A callable that creates a region
    """
    counter = itertools.count(1)

    def _create_region(slug: str | None = None, **overrides: Any) -> Region:
        n = next(counter)
        defaults: dict[str, Any] = {
            "name": f"Test Region {n}",
            "slug": slug or f"test-region-{n}",
            "status": ACTIVE,
            "administrative_division": MUNICIPALITY,
            "postal_code": "00000",
            "admin_mail": f"admin{n}@example.com",
        }
        defaults.update(overrides)
        region = Region.objects.create(**defaults)
        # Ensure the region has at least one language so default_language works
        if not LanguageTreeNode.get_root_nodes().filter(region=region).exists():
            language = create_language()
            LanguageTreeNode.add_root(language=language, region=region)
        return region

    return _create_region


@pytest.fixture()
def create_page() -> Callable[..., Page]:
    """
    Factory fixture to create a
    :class:`~integreat_cms.cms.models.pages.page.Page` via treebeard's
    ``add_root`` / ``add_child`` API.

    :return: A callable that creates a page
    """

    def _create_page(
        region: Region,
        parent: Page | None = None,
        **overrides: Any,
    ) -> Page:
        kwargs: dict[str, Any] = {"region": region}
        kwargs.update(overrides)
        if parent:
            return parent.add_child(**kwargs)
        return Page.add_root(**kwargs)

    return _create_page


@pytest.fixture()
def create_page_translation() -> Callable[..., PageTranslation]:
    """
    Factory fixture to create a
    :class:`~integreat_cms.cms.models.pages.page_translation.PageTranslation`
    with sensible defaults for all required fields.

    :return: A callable that creates a page translation
    """
    counter = itertools.count(1)

    def _create_page_translation(
        page: Page,
        language: Language | None = None,
        **overrides: Any,
    ) -> PageTranslation:
        n = next(counter)
        if language is None:
            language = page.region.default_language
        defaults: dict[str, Any] = {
            "page": page,
            "language": language,
            "title": f"Test Page {n}",
            "slug": f"test-page-{n}",
            "status": PUBLIC,
        }
        defaults.update(overrides)
        return PageTranslation.objects.create(**defaults)

    return _create_page_translation


@pytest.fixture()
def create_event() -> Callable[..., Event]:
    """
    Factory fixture to create an
    :class:`~integreat_cms.cms.models.events.event.Event` with sensible defaults
    for all required fields.

    :return: A callable that creates an event
    """

    def _create_event(
        region: Region,
        start: datetime.datetime | None = None,
        end: datetime.datetime | None = None,
        **overrides: Any,
    ) -> Event:
        utc = ZoneInfo("UTC")
        if start is None:
            start = datetime.datetime(2030, 6, 1, 10, 0, tzinfo=utc)
        if end is None:
            end = start + datetime.timedelta(hours=1)
        defaults: dict[str, Any] = {
            "region": region,
            "start": start,
            "end": end,
        }
        defaults.update(overrides)
        return Event.objects.create(**defaults)

    return _create_event


@pytest.fixture()
def create_event_translation() -> Callable[..., EventTranslation]:
    """
    Factory fixture to create an
    :class:`~integreat_cms.cms.models.events.event_translation.EventTranslation`
    with sensible defaults for all required fields.

    :return: A callable that creates an event translation
    """
    counter = itertools.count(1)

    def _create_event_translation(
        event: Event,
        language: Language | None = None,
        **overrides: Any,
    ) -> EventTranslation:
        n = next(counter)
        if language is None:
            language = event.region.default_language
        defaults: dict[str, Any] = {
            "event": event,
            "language": language,
            "title": f"Test Event {n}",
            "slug": f"test-event-{n}",
        }
        defaults.update(overrides)
        return EventTranslation.objects.create(**defaults)

    return _create_event_translation


@pytest.fixture()
def create_recurrence_rule() -> Callable[..., RecurrenceRule]:
    """
    Factory fixture to create a
    :class:`~integreat_cms.cms.models.events.recurrence_rule.RecurrenceRule`.

    :return: A callable that creates a recurrence rule
    """

    def _create_recurrence_rule(**overrides: Any) -> RecurrenceRule:
        defaults: dict[str, Any] = {
            "frequency": "WEEKLY",
            "interval": 1,
        }
        defaults.update(overrides)
        return RecurrenceRule.objects.create(**defaults)

    return _create_recurrence_rule


@pytest.fixture()
def create_user() -> Callable[..., User]:
    """
    Factory fixture to create a
    :class:`~integreat_cms.cms.models.users.user.User`.

    :return: A callable that creates a user
    """
    counter = itertools.count(1)

    def _create_user(username: str | None = None, **overrides: Any) -> User:
        n = next(counter)
        defaults: dict[str, Any] = {
            "username": username or f"testuser{n}",
            "email": f"testuser{n}@example.com",
            "password": "test-password-1234!",
        }
        defaults.update(overrides)
        return User.objects.create_user(**defaults)

    return _create_user
