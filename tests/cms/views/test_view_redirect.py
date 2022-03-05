import pytest

from django.urls import reverse

from .view_config import PARAMETRIZED_REDIRECT_VIEWS


@pytest.mark.django_db
@pytest.mark.parametrize("view_name,kwargs,roles,target", PARAMETRIZED_REDIRECT_VIEWS)
def test_view_redirect(login_role_user, view_name, kwargs, roles, target):
    """
    This test checks whether the given view redirects to the given target url

    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :type login_role_user: tuple

    :param view_name: The identifier of the view
    :type view_name: str

    :param kwargs: The keyword argument passed to the view
    :type kwargs: dict

    :param roles: The list of roles which should experience the redirect
    :type roles: list

    :param target: The expected redirection target url
    :type target: str
    """
    client, role = login_role_user
    # For redirection checks, we only test the given roles
    if role in roles:
        url = reverse(view_name, kwargs=kwargs)
        response = client.get(url)
        print(response.headers)
        assert response.status_code == 302
        assert response.headers.get("location") == target
