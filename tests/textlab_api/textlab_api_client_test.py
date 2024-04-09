from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING

import pytest
from django.http import HttpResponse
from django.test.client import Client
from django.urls import reverse
from werkzeug.wrappers import Request, Response

from integreat_cms.cms.constants import status
from integreat_cms.cms.constants.roles import EDITOR
from integreat_cms.cms.models.pages.page import Page
from integreat_cms.cms.models.pages.page_translation import PageTranslation
from integreat_cms.cms.models.regions.region import Region

if TYPE_CHECKING:
    from django.test.client import Client
    from pytest_django.fixtures import SettingsWrapper
    from pytest_httpserver.httpserver import HTTPServer


TEXTLAB_API_MOCK_DATA = [
    (
        # Textlab API returns an error response with the message attribute (on login request)
        400,
        {"message": "Invalid username/password supplied"},
        200,
        {"formulaHix": 15.489207},
    ),
    (
        # Textlab API returns an error response with the message attribute (on benchmark request)
        200,
        {"token": "dummy"},
        400,
        {"message": "Error occured"},
    ),
    (
        # Textlab API returns an error response without the message attribute
        200,
        {"token": "dummy"},
        500,
        {"attr": "Error occured"},
    ),
    (
        # Textlab API returns an error response with plain text in the response body
        200,
        {"token": "dummy"},
        500,
        "Error occured",
    ),
    (
        # Textlab API returns a successful response without the formulaHix attribute
        200,
        {"token": "dummy"},
        200,
        {"attr": 15.489207},
    ),
]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "login_status_code, login_response_body, benchmark_status_code, benchmark_response_body",
    TEXTLAB_API_MOCK_DATA,
)
def test_get_hix_score_errors(
    load_test_data: None,
    admin_client: Client,
    settings: SettingsWrapper,
    httpserver: HTTPServer,
    login_status_code: int,
    login_response_body: dict[str, str],
    benchmark_status_code: int,
    benchmark_response_body: dict[str, str],
) -> None:

    # Setup a mocked Textlab API server
    httpserver.expect_request("/user/login").respond_with_json(
        login_response_body, status=login_status_code
    )

    def benchmark_handler(request: Request) -> Response:
        if isinstance(benchmark_response_body, dict):
            return Response(
                json.dumps(benchmark_response_body), status=benchmark_status_code
            )
        else:
            return Response(benchmark_response_body, status=benchmark_status_code)

    httpserver.expect_request(
        f"/benchmark/{settings.TEXTLAB_API_DEFAULT_BENCHMARK_ID}"
    ).respond_with_handler(benchmark_handler)

    # Redirect call aimed at the Textlab API to the fake server
    settings.TEXTLAB_API_URL = f"http://localhost:{httpserver.port}"

    # Get HIX score
    get_hix_score = reverse(
        "get_hix_score",
        kwargs={
            "region_slug": "augsburg",
        },
    )

    response = admin_client.post(
        get_hix_score,
        data={"text": "<p>Seiteninhalt</p>"},
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.json() == {"error": "Could not retrieve hix score"}
