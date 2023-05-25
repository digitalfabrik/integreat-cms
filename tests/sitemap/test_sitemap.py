import pytest
from django.test.client import Client

from .sitemap_config import SITEMAPS


@pytest.mark.django_db
@pytest.mark.parametrize("url,expected_sitemap,expected_queries", SITEMAPS)
def test_sitemap(
    load_test_data,
    django_assert_num_queries,
    url,
    expected_sitemap,
    expected_queries,
):
    """
    This test class checks all URLs defined in :attr:`~tests.sitemap.sitemap_config.SITEMAPS`.
    It verifies that the content delivered by the sitemap is equivalent with the data
    provided in the corresponding xml file.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :type load_test_data: tuple

    :param django_assert_num_queries: The fixture providing the query assertion
    :type django_assert_num_queries: functools.partialmethod

    :param url: The url of the sitemap
    :type url: str

    :param expected_sitemap: The path to the xml file that contains the expected sitemap
    :type expected_sitemap: str

    :param expected_queries: The expected number of SQL queries
    :type expected_queries: int
    """
    client = Client()
    with django_assert_num_queries(expected_queries):
        response = client.get(url)
    print(response.headers)
    assert response.status_code == 200
    with open(expected_sitemap, encoding="utf-8") as f:
        assert f.read() == response.content.decode()
