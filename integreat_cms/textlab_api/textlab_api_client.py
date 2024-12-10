from __future__ import annotations

import json
import logging
from html import unescape
from typing import TYPE_CHECKING, TypedDict
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .utils import format_hix_feedback

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)


class TextlabResult(TypedDict):
    """
    The result that is returned from the textlab api via `benchmark`.
    """

    score: float | None
    feedback: list[dict[str, Any]]


class TextlabClient:
    """
    Client for the textlab api.
    Supports login and hix-score retrieval.

    A detailed API documentation can be found at https://comlab-ulm.github.io/swagger-V8/
    """

    def __init__(self, username: str, password: str) -> None:
        if not settings.TEXTLAB_API_ENABLED:
            raise ImproperlyConfigured("Textlab API is disabled")

        self.username = username
        self.password = password
        self.token = None

        self.login()

    def login(self) -> None:
        """
        Authorizes for the textlab api. On success, sets the token attribute.

        :raises urllib.error.HTTPError: If the login was not successful
        """
        data = {"identifier": self.username, "password": self.password}
        response = self.post_request("/user/login", data)
        self.token = response["token"]

    def benchmark(
        self,
        text: str,
        text_type: int = settings.TEXTLAB_API_DEFAULT_BENCHMARK_ID,
    ) -> TextlabResult:
        """
        Retrieves the hix score of the given text.

        :param text: The text to calculate the score for
        :param text_type: The id of the text type ("Textsorte") or, in terms of the api, benchmark to query.
            A benchmark is a pre-defined set of modules producing various metrics.
            They can have threshold/target values, depending on the type of text the benchmark is trying to represent.
            The available text types activated for the logged in account can be queried by sending a simple
            GET request to the ``/benchmark`` endpoint, complete with all metrics that get included for it.
            You can find the not so helpful API "documentation" here: https://comlab-ulm.github.io/swagger-V8/
            But since for now we are only interested in the HIX score anyway, we just use the benchmark
            "Letter Demo Integreat" with ID ``420`` by default.
        :return: The textlab result including score and feedback, or None if an error occurred
        """
        data = {"text": unescape(text), "locale_name": "de_DE"}
        path = f"/benchmark/{text_type}"
        response = self.post_request(path, data, self.token)

        feedback_details = format_hix_feedback(response)

        return {
            "score": response.get("formulaHix"),
            "feedback": feedback_details,
        }

    @staticmethod
    def post_request(
        path: str,
        data: dict[str, str],
        auth_token: str | None = None,
    ) -> dict[str, Any]:
        """
        Sends a request to the api.

        :param path: The api path
        :param data: The data to send
        :param auth_token: The authorization token to use
        :return: The response json dictionary
        :raises urllib.error.HTTPError: If the request failed
        """
        data_json: bytes = json.dumps(data).encode("utf-8")

        url = f"{settings.TEXTLAB_API_URL.rstrip('/')}{path}"
        if not url.startswith(("http:", "https:")):
            raise ValueError("URL must start with 'http:' or 'https:'")
        request = Request(  # noqa: S310
            url,
            data=data_json,
            method="POST",
        )
        if auth_token:
            request.add_header("authorization", f"Bearer {auth_token}")
        request.add_header("Content-Type", "application/json")
        request.add_header("User-Agent", "")
        with urlopen(request) as response:  # noqa: S310
            return json.loads(response.read().decode("utf-8"))
