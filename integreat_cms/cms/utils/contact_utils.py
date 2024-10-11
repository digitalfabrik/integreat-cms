from __future__ import annotations

from html.parser import HTMLParser
from typing import TYPE_CHECKING

from django.contrib.contenttypes.models import ContentType

from ..models import ContactUsage

if TYPE_CHECKING:
    from typing import Any, Iterable

    from django.db.models.base import ModelBase
    from django.db.models.query import QuerySet


class ContactLister(HTMLParser):
    """
    A parser to extract ids of embedded contacts from content
    """

    def __init__(self) -> None:
        self.in_contact = False
        self.id: str | None = ""
        super().__init__()

    def reset(self) -> None:
        """
        Reset the parser (cheaper than creating a new instance)
        """
        HTMLParser.reset(self)
        self.ids: list[str | None] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """
        Called whenever we encounter a start tag

        Check whether we are at a div with ``data-contact`` and remember the id
        """
        if tag == "div":
            if contact := [v for k, v in attrs if k == "data-contact"]:
                self.in_contact = True
                self.id = contact[0]

    def handle_endtag(self, tag: str) -> None:
        """
        Called whenever we encounter an end tag
        """
        if tag == "div" and self.in_contact:
            # This is not very spectacular since all the important parts are in the start tag
            self.ids.append(self.id)
            self.in_contact = False
            self.id = ""

    def handle_data(self, data: Any) -> None:
        """
        Called whenever we encounter data (like text)
        """
        if self.in_contact:
            # Ignoring data inside contact since we only care about the id
            pass


def parse_contacts(obj: ModelBase, field: str) -> list[str | None]:
    """
    Get the field from the object and extract the contact ids
    """
    parser = ContactLister()
    if html := getattr(obj, field):
        parser.feed(html)
        parser.close()
    return parser.ids
