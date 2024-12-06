from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

import pytest
from django.test.client import Client

from .api_config import API_ENDPOINTS


@pytest.mark.django_db
@pytest.mark.parametrize(
    "endpoint,wp_endpoint,expected_result,expected_code,expected_queries", API_ENDPOINTS
)
def test_api_result(
    load_test_data: None,
    django_assert_num_queries: Callable,
    endpoint: str,
    wp_endpoint: str,
    expected_result: str,
    expected_code: int,
    expected_queries: int,
) -> None:
    # pylint: disable=too-many-positional-arguments
    """
    This test class checks all endpoints defined in :attr:`~tests.api.api_config.API_ENDPOINTS`.
    It verifies that the content delivered by the endpoint is equivalent with the data
    provided in the corresponding json file.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param django_assert_num_queries: The fixture providing the query assertion
    :param endpoint: The url of the new Django pattern
    :param wp_endpoint: The legacy url of the wordpress endpoint pattern
    :param expected_result: The path to the json file that contains the expected result
    :param expected_code: The expected HTTP status code
    :param expected_queries: The expected number of SQL queries
    """
    client = Client()
    with django_assert_num_queries(expected_queries):
        response = client.get(endpoint, format="json")
    print(response.headers)
    assert response.status_code == expected_code
    with django_assert_num_queries(expected_queries):
        response_wp = client.get(wp_endpoint, format="json")
    print(response_wp.headers)
    assert response_wp.status_code == expected_code
    with open(expected_result, encoding="utf-8") as f:
        result = json.load(f)
        assert result == response.json()
        assert result == response_wp.json()
