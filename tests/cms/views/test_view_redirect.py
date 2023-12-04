from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.test.client import Client
from django.urls import reverse

from .view_config import PARAMETRIZED_REDIRECT_VIEWS

if TYPE_CHECKING:
    from typing import Any

    from _pytest.logging import LogCaptureFixture

    from .view_config import RedirectTarget, Roles, ViewKwargs, ViewNameStr


@pytest.mark.django_db
@pytest.mark.parametrize("view_name,kwargs,roles,target", PARAMETRIZED_REDIRECT_VIEWS)
def test_view_redirect(
    login_role_user: tuple[Client, str],
    caplog: LogCaptureFixture,
    view_name: ViewNameStr,
    kwargs: ViewKwargs,
    roles: Roles,
    target: RedirectTarget,
) -> None:
    """
    This test checks whether the given view redirects to the given target url

    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :param caplog: The :fixture:`caplog` fixture
    :param view_name: The identifier of the view
    :param kwargs: The keyword argument passed to the view
    :param roles: The list of roles which should experience the redirect
    :param target: The expected redirection target url
    """
    client, role = login_role_user
    # For redirection checks, we only test the given roles
    if role in roles:
        url = reverse(view_name, kwargs=kwargs)
        response = client.get(url)
        print(response.headers)
        assert response.status_code == 302
        assert response.headers.get("location") == target
