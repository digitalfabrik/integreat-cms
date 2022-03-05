import pytest

from django.test.client import Client
from django.urls import resolve, reverse

from integreat_cms.cms.models import Page


# pylint: disable=unused-argument
@pytest.mark.django_db
def test_api_push_page_content(load_test_data):
    """
    This test class checks all endpoints defined in :attr:`~tests.api.api_config.API_ENDPOINTS`.
    It verifies that the content delivered by the endpoint is equivalent with the data
    provided in the corresponding json file.

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :type load_test_data: tuple
    """
    client = Client()
    valid_token = "valid-token"
    invalid_token = "invalid-token"
    new_content = "<p>new content</p>"
    view_name = "api:push_page_translation_content"
    endpoint = reverse(
        view_name, kwargs={"region_slug": "augsburg", "language_slug": "de"}
    )
    # Check whether the endpoints resolve correctly
    match = resolve("/api/augsburg/de/pushpage/")
    wp_match = resolve("/augsburg/de/wp-json/extensions/v3/pushpage/")
    assert match.view_name == wp_match.view_name == view_name
    # Test invalid submission
    response = client.post(
        endpoint,
        {"content": new_content, "token": invalid_token},
        format="json",
        content_type="application/json",
    )
    print(response.headers)
    assert response.status_code == 403
    assert response.json() == {"status": "denied"}
    assert not Page.objects.filter(api_token=invalid_token).exists()
    # Test valid submission
    page = Page.objects.get(api_token=valid_token)
    assert page.get_translation("de").content != new_content
    response = client.post(
        endpoint,
        {"content": new_content, "token": valid_token},
        format="json",
        content_type="application/json",
    )
    print(response.headers)
    assert response.status_code == 200
    assert response.json() == {"status": "success"}
    page = Page.objects.get(api_token=valid_token)
    assert page.get_translation("de").content == new_content
