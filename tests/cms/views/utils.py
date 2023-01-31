from django.conf import settings
from django.urls import reverse

from ...conftest import ANONYMOUS


def check_view_status_code(login_role_user, view_name, kwargs, post_data, roles):
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
                assert response.status_code in [
                    200,
                    201,
                ], f"JSON view {view_name} returned status code {response.status_code} instead of 200 or 201 for role {role}"
            else:
                # Normal post-views should redirect after a successful operation (200 usually mean form errors)
                assert (
                    response.status_code == 302
                ), f"POST view {view_name} returned status code {response.status_code} instead of 302 for role {role}"
        else:
            # Get-views should return 200
            assert (
                response.status_code == 200
            ), f"GET view {view_name} returned status code {response.status_code} instead of 200 for role {role}"
    elif role == ANONYMOUS:
        # For anonymous users, we want to redirect to the login form instead of showing an error

        assert (
            response.status_code == 302
        ), f"View {view_name} did not enforce access control for anonymous users (status code {response.status_code} instead of 302)"
        assert (
            response.headers.get("location") == f"{settings.LOGIN_URL}?next={url}"
        ), f"View {view_name} did not redirect to login for anonymous users (location header {response.headers.get('location')})"
    else:
        # For logged in users, we want to show an error if they get a permission denied
        assert (
            response.status_code == 403
        ), f"View {view_name} did not enforce access control for role {role} (status code {response.status_code} instead of 403)"
