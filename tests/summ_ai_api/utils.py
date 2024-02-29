from collections.abc import Callable
from unittest.mock import MagicMock, Mock

import aiohttp
from aiohttp.web import Application as aiohttpApplication
from aiohttp.web_request import BaseRequest, Request
from aiohttp.web_response import Response
from asgiref.sync import sync_to_async
from pytest_django.fixtures import SettingsWrapper

from integreat_cms.cms.constants import machine_translation_permissions as mt_perms
from integreat_cms.cms.models import Page, Region


def make_mock_summ_ai_server(response_data: dict, status: int = 200) -> Callable:
    """
    Creates a mock of SummAiServer-(Response)

    :param response_data: data that mocked server returns
    :param status: http status code that mocked server returns (default = 200)
    :return: Request handler for mocked SummAiServer
    """

    async def fake_summ_ai_server(request: BaseRequest) -> Response:
        """
        Create fake responses which simulate the SUMM.AI API server

        :param request: The request
        :return: The response
        """
        return aiohttp.web.json_response(data=response_data, status=status)

    return fake_summ_ai_server


def make_mock_summ_ai_server_rate_limited() -> aiohttpApplication:
    """
    Creates a mock of SUMM.AI server with rate limiting

    :return: Mocked SUMM.AI server with rate limiting
    """
    app = aiohttp.web.Application()
    app["attempt"] = 0

    async def fake_summ_ai_server_rate_limited(request: Request) -> Response:
        request.app["attempt"] += 1
        if request.app["attempt"] < 2:
            # What if we get rate limited?
            return aiohttp.web.json_response(
                data={"error": "rate limit exceeded"}, status=429
            )
        if request.app["attempt"] == 2:
            # What if we get invalid JSON?
            return aiohttp.web.Response(
                text='{"incomplete json response": ', status=200
            )
        return aiohttp.web.json_response(
            data={
                "translated_text": "Hier ist Ihre Leichte Sprache Übersetzung",
                "jobid": "9999",
            },
            status=200,
        )

    app.router.add_post("/", fake_summ_ai_server_rate_limited)
    return app


def make_rogue_summ_ai_server(response_text: str, status: int = 200) -> Callable:
    """
    Creates a mock of SummAiServer-(Response)
    that can return any text as response (not just JSON)

    :param response_text: text that mocked server returns
    :param status: http status code that mocked server returns (default = 200)
    :return: Request handler for mocked SummAiServer
    """

    async def rogue_summ_ai_server(request: BaseRequest) -> Response:
        """
        Create text responses which simulate the SUMM.AI API server

        :param request: The request
        :return: The response
        """
        return aiohttp.web.Response(text=response_text, status=status)

    return rogue_summ_ai_server


@sync_to_async
def enable_summ_api(region_slug: str) -> None:
    """
    Enable SUMM.AI in the test region

    :param region_slug: The slug of the region in which we want to enable SUMM.AI
    """
    # Enable SUMM.AI in the test region without changing last_updated field
    # to prevent race conditions with other tests
    Region.objects.filter(slug=region_slug).update(summ_ai_enabled=True)


@sync_to_async
def get_changed_pages(settings: SettingsWrapper, ids: list[int]) -> list[dict]:
    """
    Load the changed pages with the specified ids from the database

    :param settings: The fixture providing the django settings
    :param ids: A list containing the requested pages including their translations in German and Easy German
    :return: The changed pages
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


# pylint: disable=too-few-public-methods
class MockedRequest:
    """
    Helper class mocking request, used for creating a SummAiApiclient instance. Region-property is needed therefore.
    """

    def __init__(self) -> None:
        self.user = MagicMock()
        self.user.has_perm = Mock(return_value=True)
        self.region = MockedRegion()
        self.data = {"dummy": "dummy request"}


# pylint: disable=too-few-public-methods, missing-class-docstring
class MockedRegion:
    def __init__(self) -> None:
        self.id = 1
        self.slug = "augsburg"
        self.summ_ai_enabled = True
        self.machine_translate_pages = mt_perms.EVERYONE
