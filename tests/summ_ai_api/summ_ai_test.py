import pytest

from asgiref.sync import sync_to_async
from aiohttp import web

from django.urls import reverse

from integreat_cms.cms.models import Page, Region

from ..conftest import (
    ANONYMOUS,
    PRIV_STAFF_ROLES,
    MANAGEMENT,
    EDITOR,
    AUTHOR,
)


async def fake_summ_ai_server(request):
    """
    Create fake responses which simulate the SUMM.AI API server

    :param request: The request
    :type request: aiohttp.web.Request

    :return: The response
    :rtype: aiohttp.web.Response
    """
    return web.json_response(
        {
            "translated_text": "Hier ist Ihre Leichte Sprache Übersetzung",
            "jobid": "9999",
        }
    )


@sync_to_async
def enable_summ_api(region_slug):
    """
    Enable SUMM.AI in the test region

    :param region_slug: The slug of the region in which we want to enable SUMM.AI
    :type region_slug: str
    """
    # Enable SUMM.AI in the test region without changing last_updated field
    # to prevent race conditions with other tests
    Region.objects.filter(slug=region_slug).update(summ_ai_enabled=True)


@sync_to_async
def get_changed_pages(settings, ids):
    """
    Load the changed pages with the specified ids from the database

    :param settings: The fixture providing the django settings
    :type settings: :fixture:`settings`

    :param ids: A list containing the requested pages including their translations in German and Easy German
    :type ids: list [ int ]

    :return: The changed pages
    :rtype: list [ dict ]
    """
    # Enable SUMM.AI in the test region
    return [
        {
            "page": page,
            **{
                slug: page.get_translation(slug)
                for slug in [
                    settings.SUMM_AI_GERMAN_LANGUAGE_SLUG,
                    settings.SUMM_AI_EASY_GERMAN_LANGUAGE_SLUG,
                ]
            },
        }
        for page in Page.objects.filter(id__in=ids)
    ]


@pytest.mark.django_db
# pylint: disable=too-many-locals
async def test_auto_translate_easy_german(
    login_role_user_async, settings, aiohttp_raw_server
):
    """
    This test checks whether the SUMM.AI API client works as expected

    :param login_role_user_async: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :type login_role_user_async: tuple

    :param settings: The fixture providing the django settings
    :type settings: :fixture:`settings`

    :param aiohttp_raw_server: The fixture providing the dummy aiohttp server used for faking the SUMM.AI API server
    :type aiohttp_raw_server: :data:`aiohttp:pytest_aiohttp.aiohttp_raw_server`
    """
    # The region we want to use for testing
    region_slug = "augsburg"
    # Enable SUMM.AI in the test region
    await enable_summ_api(region_slug)
    # Setup a dummy server to fake responses from the SUMM.AI API server (an instance of aiohttp.test_utils.RawTestServer)
    fake_server = await aiohttp_raw_server(fake_summ_ai_server)
    # Redirect call to the SUMM.AI API to the fake server
    settings.SUMM_AI_API_URL = (
        f"{fake_server.scheme}://{fake_server.host}:{fake_server.port}"
    )
    # Test for english messages
    settings.LANGUAGE_CODE = "en"
    # Log the user in
    client, role = login_role_user_async
    # Translate the pages
    selected_ids = [1, 2, 3]
    translate_easy_german = reverse(
        "auto_translate_easy_german_pages",
        kwargs={"region_slug": region_slug, "language_slug": "de"},
    )
    response = await client.post(
        translate_easy_german, data={"selected_ids[]": selected_ids}
    )
    print(response.headers)
    if role in PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR]:
        # If the role should be allowed to access the view, we expect a successful result
        assert response.status_code == 302
        page_tree = reverse(
            "pages", kwargs={"region_slug": region_slug, "language_slug": "de"}
        )
        assert response.headers.get("Location") == page_tree
        response = await client.get(page_tree)
        print(response.headers)
        # Get the page objects including their translations from the database
        changed_pages = await get_changed_pages(settings, selected_ids)
        for page in changed_pages:
            # Check that the success message are present
            assert (
                f'Page "{page[settings.SUMM_AI_GERMAN_LANGUAGE_SLUG]}" has been successfully translated into Easy German.'
                in response.content.decode("utf-8")
            )
            # Check that the page translation exists and really has the correct content
            assert (
                "Hier ist Ihre Leichte Sprache &#220;bersetzung"
                in page[settings.SUMM_AI_EASY_GERMAN_LANGUAGE_SLUG].content
            )
    elif role == ANONYMOUS:
        # For anonymous users, we want to redirect to the login form instead of showing an error
        assert response.status_code == 302
        assert (
            response.headers.get("location")
            == f"{settings.LOGIN_URL}?next={translate_easy_german}"
        )
    else:
        # For logged in users, we want to show an error if they get a permission denied
        assert response.status_code == 403


async def broken_fake_summ_ai_server(request):
    """
    Create fake responses which simulate the SUMM.AI API server

    :param request: The request
    :type request: aiohttp.web.Request

    :return: The response
    :rtype: aiohttp.web.Response
    """
    return web.json_response(
        data={
            "error": "An error occurred",
        },
        status=500,
    )


# pylint: disable=unused-argument,too-many-locals
@pytest.mark.django_db
async def test_summ_ai_error_handling(
    login_role_user_async, settings, aiohttp_raw_server
):
    """
    This test checks whether the error handling of the SUMM.AI API client works as expected

    :param login_role_user_async: The fixture providing the http client and the current role (see :meth:`~tests.conftest.login_role_user`)
    :type login_role_user_async: tuple

    :param settings: The fixture providing the django settings
    :type settings: :fixture:`settings`

    :param aiohttp_raw_server: The fixture providing the dummy aiohttp server used for faking the SUMM.AI API server
    :type aiohttp_raw_server: :data:`aiohttp:pytest_aiohttp.aiohttp_raw_server`
    """
    # The region we want to use for testing
    region_slug = "augsburg"
    # Setup a dummy server to fake responses from the SUMM.AI API server (an instance of aiohttp.test_utils.RawTestServer)
    fake_server = await aiohttp_raw_server(broken_fake_summ_ai_server)
    # Enable SUMM.AI in the test region
    await enable_summ_api(region_slug)
    # Redirect call to the SUMM.AI API to the fake server
    settings.SUMM_AI_API_URL = (
        f"{fake_server.scheme}://{fake_server.host}:{fake_server.port}"
    )
    # Test for english messages
    settings.LANGUAGE_CODE = "en"
    # Log the user in
    client, role = login_role_user_async
    # Translate the pages
    translate_easy_german = reverse(
        "auto_translate_easy_german_pages",
        kwargs={"region_slug": region_slug, "language_slug": "de"},
    )
    response = await client.post(translate_easy_german, data={"selected_ids[]": [1]})
    print(response.headers)
    if role in PRIV_STAFF_ROLES + [MANAGEMENT, EDITOR, AUTHOR]:
        # If the role should be allowed to access the view, we expect a redirect to the page tree
        assert response.status_code == 302
        page_tree = reverse(
            "pages", kwargs={"region_slug": region_slug, "language_slug": "de"}
        )
        assert response.headers.get("Location") == page_tree
        response = await client.get(page_tree)
        print(response.headers)
        # Check that the error message is present
        assert (
            "could not be automatically translated into Easy German."
            in response.content.decode("utf-8")
        )
