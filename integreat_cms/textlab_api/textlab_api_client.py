import json
import logging
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from html import unescape

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


logger = logging.getLogger(__name__)


class TextlabClient:
    """
    Client for the textlab api.
    Supports login and hix-score retrieval.
    """

    def __init__(self, username, password):
        if not settings.TEXTLAB_API_ENABLED:
            raise ImproperlyConfigured("Textlab API is disabled")

        self.username = username
        self.password = password
        self.token = None

        self.login()

    def login(self):
        """
        Authorizes for the textlab api. On success, sets the token attribute.

        :raises urllib.error.HTTPError: If the login was not successful
        """
        data = {"identifier": self.username, "password": self.password}
        response = self.post_request("/user/login", data)
        self.token = response["token"]

    def benchmark(self, text):
        """
        Retrieves the hix score of the given text.

        :param text: The text to calculate the score for
        :type text: str

        :return: The score, or None if an error occurred
        :rtype: float

        :raises urllib.error.HTTPError: if an http error occurred
        """
        data = {"text": unescape(text), "locale_name": "de_DE"}
        path = "/benchmark/5"
        try:
            response = self.post_request(path, data, self.token)
        except HTTPError:
            return None
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

        :return: The response json dictionary
        :rtype: dict

        :raises urllib.error.HTTPError: If the request failed
        """
        data = json.dumps(data).encode("utf-8")
        request = Request(
            f"{settings.TEXTLAB_API_URL.rstrip('/')}{path}", data=data, method="POST"
        )
        if auth_token:
            request.add_header("authorization", f"Bearer {auth_token}")
        request.add_header("Content-Type", "application/json")
        with urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
