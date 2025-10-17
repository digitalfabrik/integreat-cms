"""
This module contains shared fixtures for pytest
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test.client import AsyncClient, Client

from integreat_cms.cms.constants.roles import (
    APP_TEAM,
    AUTHOR,
    CMS_TEAM,
    EDITOR,
    EVENT_MANAGER,
    MANAGEMENT,
    MARKETING_TEAM,
    OBSERVER,
    SERVICE_TEAM,
)
from integreat_cms.firebase_api.firebase_security_service import FirebaseSecurityService
from tests.mock import MockServer

if TYPE_CHECKING:
    from collections.abc import Generator
    from typing import Final

    from _pytest.fixtures import SubRequest
    from pytest_django.fixtures import SettingsWrapper
    from pytest_django.plugin import _DatabaseBlocker  # type: ignore[attr-defined]
    from pytest_httpserver.httpserver import HTTPServer


#: A role identifier for superusers
ROOT: Final = "ROOT"
#: A role identifier for anonymous users
ANONYMOUS: Final = "ANONYMOUS"

#: All roles with editing permissions
WRITE_ROLES: Final = [MANAGEMENT, EDITOR, AUTHOR, EVENT_MANAGER]
#: All roles of region users
REGION_ROLES: Final = [*WRITE_ROLES, OBSERVER]
#: All roles of staff users
STAFF_ROLES: Final = [ROOT, SERVICE_TEAM, CMS_TEAM, APP_TEAM, MARKETING_TEAM]
#: All roles of staff users that don't just have read-only permissions
PRIV_STAFF_ROLES: Final = [ROOT, APP_TEAM, SERVICE_TEAM, CMS_TEAM]
#: All roles of staff users that don't just have read-only permissions
HIGH_PRIV_STAFF_ROLES: Final = [ROOT, SERVICE_TEAM, CMS_TEAM]
#: All region and staff roles
ROLES: Final = REGION_ROLES + STAFF_ROLES
#: All region and staff roles and anonymous users
ALL_ROLES: Final = [*ROLES, ANONYMOUS]

#: Enable the aiohttp pytest plugin to make use of the test server
pytest_plugins: Final = "aiohttp.pytest_plugin"


@pytest.fixture(scope="session")
def load_test_data(django_db_setup: None, django_db_blocker: _DatabaseBlocker) -> None:
    """
    Load the test data initially for all test cases

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
    Load the test data initially for all transactional test cases

    :param transactional_db: The fixture providing transaction support for the database
    :param django_db_blocker: The fixture providing the database blocker
    """
    with django_db_blocker.unblock():
        call_command("loaddata", "integreat_cms/cms/fixtures/test_roles.json")
        call_command("loaddata", "integreat_cms/cms/fixtures/test_data.json")


@pytest.fixture(scope="session", params=ALL_ROLES)
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


@pytest.fixture(scope="session", params=ALL_ROLES)
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

def pytest_collection_modifyitems(items):
    DESIRED_ORDER = [
        "tests.cms.views.status_code.test_view_status_code_11",
        "tests.pdf.test_pdf_export",
        "tests.cms.test_media_library",
        "tests.cms.test_page_filters",
        "test_hix",
        "test_poi_category_form_view",
        "tests.cms.views.test_public_view_status_code",
        "tests.core.management.commands.test_summ_ai_bulk",
    ]

    def module_name(item):
        return item.module.__name__

    sorted_items = []
    remaining = items.copy()

    for module in DESIRED_ORDER:
        matching = [it for it in remaining if module_name(it) == module]
        remaining = [it for it in remaining if module_name(it) != module]
        sorted_items.extend(matching)

    print(sorted_items)

    items[:] = sorted_items