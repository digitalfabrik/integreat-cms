import pytest
from django.test.client import Client
from django.urls import reverse

from ...utils import assert_no_error_messages
from .view_config import PARAMETRIZED_PUBLIC_VIEWS


@pytest.mark.django_db
@pytest.mark.parametrize("view_name,post_data", PARAMETRIZED_PUBLIC_VIEWS)
def test_public_view_status_code(load_test_data, caplog, view_name, post_data):
    """
    This test checks whether the given view return the correct status code for anonymous users

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :type load_test_data: NoneType

    :param caplog: The :fixture:`caplog` fixture
    :type caplog: pytest.LogCaptureFixture

    :param view_name: The identifier of the view
    :type view_name: str

    :param post_data: The post data for this view
    :type post_data: dict
    """
    client = Client()
    url = reverse(view_name)
    response = client.post(url, data=post_data) if post_data else client.get(url)
    print(response.headers)
    assert_no_error_messages(caplog)
    if post_data:
        # Post-views should redirect after a successful operation
        assert response.status_code == 302
    else:
        # Get-views should return 200
        assert response.status_code == 200
