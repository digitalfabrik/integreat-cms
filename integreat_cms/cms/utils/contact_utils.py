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


class Contactlist:
    """
    An abstract class for easily tracking where contacts are embedded for a specific content type.
    Inspired by the linklists of :mod:`linkcheck`

    You can override object_filter and object_exclude in a contactlist class.
    Just provide a dictionary to be used as a Django lookup filter.
    Only objects that pass the filter will be queried for contacts.
    This doesn't affect whether an object is regarded as a valid contact target. Only as a contact source.
    Example usage in your contactlists.py:
    object_filter = {'active': True} - Would only check active objects for contacts
    """

    html_fields: list[str] = []
    model: ModelBase = NotImplemented

    object_filter: dict[str, Any] | None = None
    object_exclude: dict[str, Any] | None = None

    @classmethod
    def filter_callable(cls, objects: QuerySet) -> QuerySet:
        """
        A method for custom logic for filtering objects. A noop in this base class.
        """
        return objects

    def contacts(self, obj: ModelBase) -> list[tuple[str, str | None]]:
        """
        Compile contacts used in all ``html_field``s of the object
        """
        contacts = []

        # Look for embedded contacts in HTML fields
        for field_name in self.html_fields:
            contacts += [
                (field_name, contact_id)
                for contact_id in parse_contacts(obj, field_name)
            ]

        return contacts

    @classmethod
    def objects(cls) -> QuerySet:
        """
        Construct the queryset for all relevant objects (ìncorporating ``object_filter``, ``object_exclude`` and ``filter_callable``)
        """
        objects = cls.model.objects.all()

        if cls.object_filter is not None:
            objects = objects.filter(**cls.object_filter).distinct()
        if cls.object_exclude is not None:
            objects = objects.exclude(**cls.object_exclude).distinct()
        objects = cls.filter_callable(objects)

        return objects

    def get_contactlist(
        self, extra_filter: dict[str, Any] | None = None
    ) -> list[dict[str, str | None]]:
        """
        Extract the contact ids embedded in all relevant objects
        """
        extra_filter = extra_filter or {}

        objects = self.objects()

        if extra_filter:
            objects = objects.filter(**extra_filter)

        contactlist = [
            {
                "object": obj,
                "contacts": self.contacts(obj),
            }
            for obj in objects
        ]

        return contactlist

    @classmethod
    def content_type(cls) -> ContentType:
        """
        Retrieves the content type for the model
        """
        return ContentType.objects.get_for_model(cls.model)


def find_all_contacts(
    contactlists: Iterable[type[Contactlist]] | None = None,
) -> dict[str, dict[str, int]]:
    """
    Goes through all models registered to contain contacts, records any new contacts found
    and removes all outdated contacts
    """
    if contactlists is None:
        from ..contactlist import contactlists as lists

        contactlists = lists.values()

    before = ContactUsage.objects.count()

    for contactlist_cls in contactlists:
        for contactlist in contactlist_cls().get_contactlist():
            # Just accessing the contacts forces evaluation
            # and updates the database to reflect contacts embedded in the content
            contactlist["contacts"]

    # Calculate diff
    after = ContactUsage.objects.count()

    return {
        "contactusages": {
            "diff": after - before,
            "new_total": after,
        },
    }
