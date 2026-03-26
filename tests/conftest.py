"""
This module contains shared fixtures for pytest
"""

from __future__ import annotations

import os
from typing import Any, TYPE_CHECKING
from unittest.mock import patch

import pytest


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


from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test.client import AsyncClient, Client

from integreat_cms.cms.models import Language, Page, Region
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
    from typing import Final

    from _pytest.fixtures import SubRequest
    from pytest_django.fixtures import SettingsWrapper
    from pytest_django.plugin import _DatabaseBlocker  # type: ignore[attr-defined]
    from pytest_httpserver.httpserver import HTTPServer


#: Representative subset covering all permission boundaries (for faster local runs)
QUICK_ROLE_SET: Final = [ROOT, MANAGEMENT, AUTHOR, ANONYMOUS]
#: The roles used for parametrized tests — set QUICK_ROLES=1 to use the subset
TEST_ROLES: Final = QUICK_ROLE_SET if os.environ.get("QUICK_ROLES") else ALL_ROLES

#: Enable the aiohttp pytest plugin to make use of the test server
pytest_plugins: Final = "aiohttp.pytest_plugin"


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup: None, django_db_blocker: _DatabaseBlocker) -> None:
    """
    Override pytest-django's ``django_db_setup`` to load test data as part of
    the initial database setup. This ensures non-transactional tests always
    have data available via their session-scoped database connection.

    pytest-django automatically runs transactional tests AFTER non-transactional
    ones within each worker, so there is no risk of a transactional test flushing
    the database before a non-transactional test needs it. This eliminates the
    need for ``@pytest.mark.order`` hacks.

    :param django_db_setup: The original pytest-django fixture that creates the test database
    :param django_db_blocker: The fixture providing the database blocker
    """
    with django_db_blocker.unblock():
        call_command("loaddata", "integreat_cms/cms/fixtures/test_data.json")


@pytest.fixture(scope="session")
def load_test_data(django_db_setup: None) -> None:
    """
    Backward-compatible fixture for tests that request ``load_test_data``.
    Test data is now loaded as part of ``django_db_setup``, so this is a no-op.

    :param django_db_setup: The fixture providing the database with test data
    """


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
def mock_firebase_credentials() -> Generator[None, None, None]:
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


@pytest.fixture()
def create_page() -> Callable[..., Page]:
    def _create_page(
        region: Region | None,
        name_add: str = "",
        parent: Page | None = None,
    ) -> Page:
        return (
            parent.add_child(region=parent.region)
            if parent
            else Page.add_root(region=region)
        )

    return _create_page


@pytest.fixture()
def create_language() -> Callable[..., Language]:
    def _create_language(**kwargs: Any) -> Language:
        return Language.objects.create(**kwargs)

    return _create_language
