from __future__ import annotations

from html.parser import HTMLParser
from itertools import pairwise
from typing import TYPE_CHECKING

import pytest
from django.contrib.auth import get_user_model
from django.test.client import Client
from django.urls import reverse

from ...constants import ROOT
from .view_config import PARAMETRIZED_VIEWS

if TYPE_CHECKING:
    from typing import Final

    from .view_config import ViewKwargs, ViewName


class HeadingLevelParser(HTMLParser):
    """
    Collects the level of every heading (``h1`` to ``h6``) in document order
    """

    def __init__(self) -> None:
        super().__init__()
        self.levels: list[int] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if len(tag) == 2 and tag[0] == "h" and tag[1] in "123456":
            self.levels.append(int(tag[1]))


def _url(view_name: ViewName, kwargs: ViewKwargs) -> str:
    if isinstance(view_name, tuple):
        return f"{reverse(view_name[0], kwargs=kwargs)}?{view_name[1]}"
    return reverse(view_name, kwargs=kwargs)


#: Every view a root user can open with a GET request, once per URL
ROOT_GET_URLS: Final[list[str]] = list(
    dict.fromkeys(
        _url(view_name, kwargs)
        for view_name, kwargs, post_data, roles in PARAMETRIZED_VIEWS
        if not post_data and ROOT in roles
    )
)


@pytest.mark.django_db
@pytest.mark.parametrize("url", ROOT_GET_URLS)
def test_view_does_not_skip_heading_levels(load_test_data: None, url: str) -> None:
    """
    A page's headings must not skip a level, e.g. an ``h3`` directly after an ``h1``,
    because screen reader users navigate a page by its heading structure (see #4109)

    :param load_test_data: The fixture providing the test data (see :meth:`~tests.conftest.load_test_data`)
    :param url: The url of the view
    """
    client = Client()
    client.force_login(get_user_model().objects.get(username=ROOT.lower()))
    response = client.get(url)
    if response.status_code != 200 or "text/html" not in response.headers.get(
        "Content-Type", ""
    ):
        pytest.skip(f"{url} is not an HTML page ({response.status_code})")
    parser = HeadingLevelParser()
    parser.feed(response.content.decode())
    skipped = [
        f"h{previous} -> h{current}"
        for previous, current in pairwise(parser.levels)
        if current > previous + 1
    ]
    assert not skipped, f"{url} skips a heading level: {', '.join(skipped)}"
