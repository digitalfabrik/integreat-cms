"""
This module contains shared fixtures for pytest
"""
import pytest

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test.client import Client, AsyncClient


from integreat_cms.cms.constants.roles import (
    MANAGEMENT,
    EDITOR,
    AUTHOR,
    EVENT_MANAGER,
    OBSERVER,
    SERVICE_TEAM,
    CMS_TEAM,
    APP_TEAM,
    MARKETING_TEAM,
)

#: A role identifier for superusers
ROOT = "ROOT"
#: A role identifier for anonymous users
ANONYMOUS = "ANONYMOUS"

#: All roles with editing permissions
WRITE_ROLES = [MANAGEMENT, EDITOR, AUTHOR, EVENT_MANAGER]
#: All roles of region users
REGION_ROLES = WRITE_ROLES + [OBSERVER]
#: All roles of staff users
STAFF_ROLES = [ROOT, SERVICE_TEAM, CMS_TEAM, APP_TEAM, MARKETING_TEAM]
#: All roles of staff users that don't just have read-only permissions
PRIV_STAFF_ROLES = [ROOT, APP_TEAM, SERVICE_TEAM, CMS_TEAM]
#: All roles of staff users that don't just have read-only permissions
HIGH_PRIV_STAFF_ROLES = [ROOT, SERVICE_TEAM, CMS_TEAM]
#: All region and staff roles
ROLES = REGION_ROLES + STAFF_ROLES
#: All region and staff roles and anonymous users
ALL_ROLES = ROLES + [ANONYMOUS]

#: Enable the aiohttp pytest plugin to make use of the test server
pytest_plugins = "aiohttp.pytest_plugin"


# pylint: disable=unused-argument
@pytest.fixture(scope="session")
def load_test_data(django_db_setup, django_db_blocker):
    """
    Load the test data initially for all test cases

    :param django_db_setup: The fixture providing the database availability
    :type django_db_setup: :fixture:`django_db_setup`

    :param django_db_blocker: The fixture providing the database blocker
    :type django_db_blocker: :fixture:`django_db_blocker`
    """
    with django_db_blocker.unblock():
        call_command("loaddata", "integreat_cms/cms/fixtures/test_data.json")


# pylint: disable=unused-argument,redefined-outer-name
@pytest.fixture(scope="session", params=ALL_ROLES)
def login_role_user(request, load_test_data, django_db_blocker):
    """
    Get the test user of the current role and force a login. Gets executed only once per user.

    :param request: The request object providing the parametrized role variable through ``request.param``
    :type request: pytest.FixtureRequest

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :type load_test_data: NoneType

    :param django_db_blocker: The fixture providing the database blocker
    :type django_db_blocker: :fixture:`django_db_blocker`

    :return: The http client and the current role
    :rtype: tuple
    """
    client = Client()
    # Only log in user if the role is not anonymous
    if request.param != ANONYMOUS:
        with django_db_blocker.unblock():
            user = get_user_model().objects.get(username=request.param.lower())
            client.force_login(user)
    return client, request.param


# pylint: disable=unused-argument,redefined-outer-name
@pytest.fixture(scope="session", params=ALL_ROLES)
def login_role_user_async(request, load_test_data, django_db_blocker):
    """
    Get the test user of the current role and force a login. Gets executed only once per user.
    Identical to :meth:`~tests.conftest.login_role_user` with the difference that it returns
    an :class:`django.test.client.AsyncClient` instead of :class:`django.test.client.Client`.

    :param request: The request object providing the parametrized role variable through ``request.param``
    :type request: pytest.FixtureRequest

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :type load_test_data: NoneType

    :param django_db_blocker: The fixture providing the database blocker
    :type django_db_blocker: :fixture:`django_db_blocker`

    :return: The http client and the current role
    :rtype: tuple
    """
    async_client = AsyncClient()
    # Only log in user if the role is not anonymous
    if request.param != ANONYMOUS:
        with django_db_blocker.unblock():
            user = get_user_model().objects.get(username=request.param.lower())
            async_client.force_login(user)
    return async_client, request.param
