"""
This module contains shared fixtures for pytest
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch
from contextlib import contextmanager

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import DEFAULT_DB_ALIAS, connections
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
    test_data_db_snapshot: None,
    django_db_blocker: _DatabaseBlocker,
) -> Generator[None, tuple[Client, str], None]:
    """
    Get the test user of the current role and force a login. Gets executed only once per user.

    :param request: The request object providing the parametrized role variable through ``request.param``
    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param django_db_blocker: The fixture providing the database blocker
    :return: The http client and the current role
    """
    with contextmanager(snapshot_db)(django_db_blocker, suffix="loginroleuser"):
        client = Client()
        # Only log in user if the role is not anonymous
        if request.param != ANONYMOUS:
            with django_db_blocker.unblock():
                user = get_user_model().objects.get(username=request.param.lower())
                client.force_login(user)
        yield client, request.param


@pytest.fixture(scope="session", params=ALL_ROLES)
def login_role_user_async(
    request: SubRequest,
    test_data_db_snapshot: None,
    django_db_blocker: _DatabaseBlocker,
) -> Generator[None, tuple[AsyncClient, str], None]:
    """
    Get the test user of the current role and force a login. Gets executed only once per user.
    Identical to :meth:`~tests.conftest.login_role_user` with the difference that it returns
    an :class:`django.test.client.AsyncClient` instead of :class:`django.test.client.Client`.

    :param request: The request object providing the parametrized role variable through ``request.param``
    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param django_db_blocker: The fixture providing the database blocker
    :return: The http client and the current role
    """
    with contextmanager(snapshot_db)(django_db_blocker, suffix="loginroleuser"):
        async_client = AsyncClient()
        # Only log in user if the role is not anonymous
        if request.param != ANONYMOUS:
            with django_db_blocker.unblock():
                user = get_user_model().objects.get(username=request.param.lower())
                async_client.force_login(user)
        yield async_client, request.param


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


@pytest.fixture(scope="session")
def empty_db_snapshot(django_db_setup: None, django_db_blocker: _DatabaseBlocker) -> Generator[None, None, None]:
    yield from snapshot_db(django_db_blocker, suffix="empty")

@pytest.fixture(scope="session")
def test_data_db_snapshot(empty_db_snapshot: None, django_db_blocker: _DatabaseBlocker) -> Generator[None, None, None]:
    with contextmanager(snapshot_db)(django_db_blocker, suffix="testdata"):
        # loading it in here instead of sub-requesting the load_test_data fixture
        # means we don't mess up the parent scope and don't need an additional layer of isolation (snapshot)
        with django_db_blocker.unblock():
            call_command("loaddata", "integreat_cms/cms/fixtures/test_roles.json")
            call_command("loaddata", "integreat_cms/cms/fixtures/test_data.json")
        yield

@pytest.fixture(scope="function")
def db_snapshot(transactional_db: None, django_db_blocker: _DatabaseBlocker) -> Generator[None, None, None]:
    yield from snapshot_db(django_db_blocker, suffix="snap")


def snapshot_db(django_db_blocker: _DatabaseBlocker, suffix="snap", databases=(DEFAULT_DB_ALIAS,)) -> Generator[None, None, None]:
    prev_settings = {}
    test_database_name = None

    with django_db_blocker.unblock():
        for db_name in databases:
            conn = connections[db_name]
            prev_settings[db_name] = conn.settings_dict
            test_database_name = conn.settings_dict["NAME"]

            # SQLite in-memory requires manual cloning as Django does things a little differently
            if conn.vendor == "sqlite" and conn.is_in_memory_db():
                components = urllib.parse.urlparse(test_database_name)
                sandbox_uri = urllib.parse.urlunparse(
                    components._replace(path=f"{components.path}_{suffix}")
                )
                source = sqlite3.connect(test_database_name, uri=True)
                target = sqlite3.connect(sandbox_uri, uri=True)
                source.backup(target)
                source.close()
                conn.settings_dict["NAME"] = sandbox_uri
                conn.close()
                conn.connect()  # reconnect before closing so we don't lose the db
                target.close()

            else:
                conn.creation.clone_test_db(suffix=suffix)
                conn.settings_dict = conn.creation.get_test_db_clone_settings(
                    suffix=suffix
                )
                conn.close()  # required for MySQL

    yield

    with django_db_blocker.unblock():
        for db_name in databases:
            conn = connections[db_name]
            conn.creation.destroy_test_db(old_database_name=test_database_name)
            conn.close()
            conn.settings_dict = prev_settings[db_name]
            conn.connect()
