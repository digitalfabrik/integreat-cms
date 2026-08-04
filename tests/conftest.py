"""
This module contains shared fixtures for pytest
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest  # isort: skip — must precede local imports for fixture registration
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.test.client import AsyncClient, Client
from linkcheck.listeners import unregister_listeners

from integreat_cms.cms.models import Language
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
    from collections.abc import Generator
    from typing import Final

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


@pytest.fixture(scope="session", params=TEST_ROLES)
def login_role_user_async(
    request: SubRequest,
    load_test_data: None,
    django_db_blocker: _DatabaseBlocker,
) -> tuple[AsyncClient, str]:
    """
    Get the test user of the current role and force a login. Gets executed only once per user.
    Identical to :meth:`~tests.conftest.login_role_user` with the difference that it returns
    an :class:`django.test.client.AsyncClient` instead of :class:`django.test.client.Client`.

    :param request: The request object providing the parametrized role variable through ``request.param``
    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param django_db_blocker: The fixture providing the database blocker
    :return: The http client and the current role
    """
    async_client = AsyncClient()
    # Only log in user if the role is not anonymous
    if request.param != ANONYMOUS:
        with django_db_blocker.unblock():
            user = get_user_model().objects.get(username=request.param.lower())
            async_client.force_login(user)
    return async_client, request.param


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
    for fixture_name in ("login_role_user", "login_role_user_async"):
        if fixture_name in request.fixturenames:
            client, _role = request.getfixturevalue(fixture_name)
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


@pytest.fixture()
def disable_auto_news_reimport(settings: SettingsWrapper) -> None:
    """
    Disable re-import of external news on demand to avoid hitting the real APIs and getting real news posts
    """
    settings.EXTERNALNEWS_DISABLE_AUTO_REIMPORT = True
