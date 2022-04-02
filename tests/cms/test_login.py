import pytest

from django.contrib import auth
from django.urls import reverse


# pylint: disable=unused-argument
@pytest.mark.django_db
@pytest.mark.parametrize(
    "username", ["root", "root@root.root", "management", "management@example.com"]
)
def test_login_success(load_test_data, client, settings, username):
    """
    Test whether login via username & email works as expected

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :type load_test_data: tuple

    :param client: The fixture providing the an unauthenticated user client
    :type client: :fixture:`client`

    :param settings: The Django settings
    :type settings: :fixture:`settings`

    :param username: The username/email to use for login
    :type username: str
    """
    # Test login via username/password
    response = client.post(
        settings.LOGIN_URL, data={"username": username, "password": "root1234"}
    )
    print(response.headers)
    assert response.status_code == 302
    assert response.headers.get("location") == settings.LOGIN_REDIRECT_URL
    response = client.get(settings.LOGIN_REDIRECT_URL)
    print(response.headers)
    assert response.status_code == 302
    user = auth.get_user(client)
    assert user.is_authenticated
    if user.is_superuser or user.is_staff:
        # Root user should get redirected to the admin dashboard
        assert response.headers.get("location") == reverse("admin_dashboard")
    else:
        # Region user should get redirected to the region dashboard
        assert response.headers.get("location") == reverse(
            "dashboard", kwargs={"region_slug": "augsburg"}
        )


# pylint: disable=unused-argument
@pytest.mark.django_db
@pytest.mark.parametrize(
    "username",
    [
        "root",
        "root@root.root",
        "management",
        "management@example.com",
        "non-existing-user",
        "non-existing-email@example.com",
        "",
    ],
)
def test_login_failure(load_test_data, client, settings, username):
    """
    Test whether login with incorrect credentials does not work

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :type load_test_data: tuple

    :param client: The fixture providing the an unauthenticated user client
    :type client: :fixture:`client`

    :param settings: The Django settings
    :type settings: :fixture:`settings`

    :param username: The username/email to use for login
    :type username: str
    """
    # Test for english messages
    settings.LANGUAGE_CODE = "en"
    # Test login via username/password
    response = client.post(
        settings.LOGIN_URL, data={"username": username, "password": "incorrect"}
    )
    print(response.headers)
    assert response.status_code == 200
    assert "The username or the password is incorrect." in response.content.decode()
