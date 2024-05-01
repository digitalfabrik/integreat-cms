import json

from pytest_httpserver.httpserver import HTTPServer
from werkzeug.wrappers import Request, Response


class MockServer:
    """
    Http server instance that allowes to configure mock responses
    """

    def __init__(self, http_server: HTTPServer) -> None:
        self.requests_counter = 0
        self.http_server = http_server

    def configure(self, path: str, response_status: int, response_data: dict) -> None:
        def handler(request: Request) -> Response:
            self.requests_counter += 1
            return Response(json.dumps(response_data), status=response_status)

        self.http_server.expect_request(path).respond_with_handler(handler)

    @property
    def port(self) -> int:
        return self.http_server.port
