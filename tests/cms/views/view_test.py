import pytest

from django.conf import settings
from django.test.client import Client
from django.urls import reverse

from ...conftest import ANONYMOUS
from .view_config import (
    PARAMETRIZED_VIEWS,
    PARAMETRIZED_REDIRECT_VIEWS,
    PARAMETRIZED_PUBLIC_VIEWS,
)


@pytest.mark.django_db
@pytest.mark.parametrize("view_name,kwargs,post_data,roles", PARAMETRIZED_VIEWS)
def test_view_status_code(login_role_user, view_name, kwargs, post_data, roles):
    """
    This test checks whether the given view return the correct status code for the current role

    :param login_role_user: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :type login_role_user: tuple

    :param view_name: The identifier of the view
    :type view_name: str

    :param kwargs: The keyword argument passed to the view
    :type kwargs: dict

    :param post_data: The post data for this view
    :type post_data: dict

    :param roles: The list of roles which should be able to access this view
    :type roles: list
    """
    client, role = login_role_user
    url = reverse(view_name, kwargs=kwargs)
    if post_data:
        kwargs = {"data": post_data}
        # If the post data is a string, assume json as content type
        if isinstance(post_data, str):
            kwargs["content_type"] = "application/json"
        response = client.post(url, **kwargs)
    else:
        response = client.get(url)
    print(response.headers)
    if role in roles:
        # If the role should be allowed to access the view, we expect a successful result
        if post_data:
            if response.headers.get("Content-Type") == "application/json":
                # Json-views should return 200 or 201 CREATED (for feedback)
                assert response.status_code in [200, 201]
            else:
                # Normal post-views should redirect after a successful operation (200 usually mean form errors)
                assert response.status_code == 302
        else:
            # Get-views should return 200
            assert response.status_code == 200
    elif role == ANONYMOUS:
        # For anonymous users, we want to redirect to the login form instead of showing an error
        assert response.status_code == 302
        assert response.headers.get("location") == f"{settings.LOGIN_URL}?next={url}"
    else:
        # For logged in users, we want to show an error if they get a permission denied
        assert response.status_code == 403


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


# pylint: disable=unused-argument
@pytest.mark.django_db
@pytest.mark.parametrize("view_name,post_data", PARAMETRIZED_PUBLIC_VIEWS)
def test_public_view_status_code(load_test_data, view_name, post_data):
    """
    This test checks whether the given view return the correct status code for anonymous users

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :type load_test_data: NoneType

    :param view_name: The identifier of the view
    :type view_name: str

    :param post_data: The post data for this view
    :type post_data: dict
    """
    client = Client()
    url = reverse(view_name)
    if post_data:
        response = client.post(url, data=post_data)
    else:
        response = client.get(url)
    print(response.headers)
    if post_data:
        # Post-views should redirect after a successful operation
        assert response.status_code == 302
    else:
        # Get-views should return 200
        assert response.status_code == 200
