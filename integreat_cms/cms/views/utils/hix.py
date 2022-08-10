"""
This file contains functionality to communicate with the textlab api to get the hix-value
for a given text.
"""
from functools import lru_cache
import json
import logging
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from ....api.decorators import json_response
from ....core.settings import (
    TEXTLAB_API_URL,
    TEXTLAB_API_PASSWORD,
    TEXTLAB_API_USERNAME,
)

logger = logging.getLogger(__name__)


class TextlabClient:
    """
    Client for the textlab api.
    Supports login and hix-score retrieval.
    """

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.token = None

        self.login()

    def login(self):
        """
        Authorizes for the textlab api. On success, sets the token attribute.

        :raises ValueError: If authentification was not possible
        """
        data = {"identifier": self.username, "password": self.password, "ttl": 3600}
        status, response = self.post_request("/user/login", data)
        if status != 200:
            raise ValueError("Could not connect to textlab api")
        self.token = response["token"]

    @lru_cache(maxsize=512)
    def benchmark(self, text):
        """
        Retrieves the hix score of the given text.

        :param text: The text to calculate the score for
        :type text: str

        :return: The score
        :rtype: float

        :raises urllib.error.HTTPError: if an http error occurred
        """
        data = {"text": text, "locale_name": "de_DE"}
        path = "/benchmark/5"
        try:
            _, response = self.post_request(path, data, self.token)
        except HTTPError as e:
            if e.status == 401:
                logger.info("Re-login to textlab api")
                self.login()
                _, response = self.post_request(path, data, self.token)
            else:
                raise
        return response.get("formulaHix", None)

    @staticmethod
    def post_request(path, data, auth_token=None):
        """
        Sends a request to the api.

        :param path: The api path
        :type path: str

        :param data: The data to send
        :type data: dict

        :param auth_token: The authorization token to use
        :type auth_token: str

        :return: A tuple of status code and response json dictionary
        :rtype: tuple
        """
        data = json.dumps(data).encode("utf-8")
        request = Request(f"{TEXTLAB_API_URL}{path}", data=data, method="POST")
        if auth_token:
            request.add_header("authorization", f"Bearer {auth_token}")
        request.add_header("Content-Type", "application/json")
        with urlopen(request) as response:
            return (response.status, json.loads(response.read().decode("utf-8")))


if TEXTLAB_API_PASSWORD:
    client = TextlabClient(TEXTLAB_API_USERNAME, TEXTLAB_API_PASSWORD)
else:
    client = None


@require_POST
@json_response
def get_hix_score(request):
    """
    Calculates the hix score for the param 'text' in the request body and returns it.

    :param request: The request
    :type request: ~django.http.HttpRequest

    :return: A json response, of {"score": value} in case of success
    :rtype: ~django.http.JsonResponse
    """
    if not client:
        return JsonResponse({"error": "No textlab password set"})

    body = json.loads(request.body.decode("utf-8"))
    text = body["text"]

    if not isinstance(text, str) or not text.strip():
        return JsonResponse({"error": f"Invalid text: '{text}'"})

    score = client.benchmark(text)
    if score is not None:
        return JsonResponse({"score": score})
    return JsonResponse({"error": "Could not retrieve hix score"})
