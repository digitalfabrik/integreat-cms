from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

import pytest
from django.test.client import Client

from .api_config import API_SOCIAL_ENDPOINTS


@pytest.mark.django_db
@pytest.mark.parametrize(
    "endpoint,expected_result,expected_code,expected_queries",
    API_SOCIAL_ENDPOINTS,
)
def test_api_result(
    load_test_data: None,
    django_assert_num_queries: Callable,
    endpoint: str,
    expected_result: str,
    expected_code: int,
    expected_queries: int,
) -> None:
    """
    This test class checks all endpoints defined in :attr:`~tests.api.api_config.API_ENDPOINTS`.
    It verifies that the content delivered by the endpoint is equivalent with the data
    provided in the corresponding json file.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param django_assert_num_queries: The fixture providing the query assertion
    :param endpoint: The url of the new Django pattern
    :param expected_result: The path to the json file that contains the expected result
    :param expected_code: The expected HTTP status code
    :param expected_queries: The expected number of SQL queries
    """
    client = Client()
    with django_assert_num_queries(expected_queries):
        response = client.get(endpoint, format="html")
    print(response.headers)
    assert response.status_code == expected_code
    if not expected_result:
        return
    with open(expected_result, encoding="utf-8") as f:
        result = json.load(f)
        template_context = response.context.dicts[3]
        assert dict(template_context) == result
