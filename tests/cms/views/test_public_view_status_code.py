import pytest

from django.test.client import Client
from django.urls import reverse

from .view_config import PARAMETRIZED_PUBLIC_VIEWS


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
