import json
import pytest

from django.test.client import Client

from .api_config import API_ENDPOINTS


# pylint: disable=unused-argument
@pytest.mark.django_db
@pytest.mark.parametrize(
    "endpoint,wp_endpoint,expected_result,expected_code", API_ENDPOINTS
)
def test_api_result(
    load_test_data, endpoint, wp_endpoint, expected_result, expected_code
):
    """
    This test class checks all endpoints defined in :attr:`~tests.api.api_config.API_ENDPOINTS`.
    It verifies that the content delivered by the endpoint is equivalent with the data
    provided in the corresponding json file.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :type load_test_data: tuple

    :param endpoint: The url of the new Django pattern
    :type endpoint: str

    :param wp_endpoint: The legacy url of the wordpress endpoint pattern
    :type wp_endpoint: str

    :param expected_result: The path to the json file that contains the expected result
    :type expected_result: str

    :param expected_code: The expected HTTP status code
    :type expected_code: int
    """
    client = Client()
    response = client.get(endpoint, format="json")
    print(response.headers)
    assert response.status_code == expected_code
    response_wp = client.get(wp_endpoint, format="json")
    print(response_wp.headers)
    assert response_wp.status_code == expected_code
    with open(expected_result, encoding="utf-8") as f:
        result = json.load(f)
        assert result == response.json()
        assert result == response_wp.json()
