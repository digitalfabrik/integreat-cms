import pytest

from django.test.client import Client
from django.urls import reverse

from .api_config import API_FEEDBACK_VIEWS


# pylint: disable=unused-argument
@pytest.mark.django_db
@pytest.mark.parametrize("view_name,post_data", API_FEEDBACK_VIEWS)
def test_api_feedback(load_test_data, view_name, post_data):
    """
    This test checks whether the feedback submission returns the correct result

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :type load_test_data: NoneType

    :param view_name: The identifier of the view
    :type view_name: str

    :param post_data: The post data for this view
    :type post_data: dict
    """
    client = Client()
    url = reverse(view_name, kwargs={"region_slug": "augsburg", "language_slug": "de"})
    response = client.post(url, data=post_data)
    print(response.headers)
    assert response.status_code == 201
    assert response.json() == {"success": "Feedback successfully submitted"}
