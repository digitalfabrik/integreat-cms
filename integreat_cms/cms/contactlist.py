from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.db.models import Exists, OuterRef

from .models import (
    Event,
    EventTranslation,
    ImprintPageTranslation,
    LanguageTreeNode,
    Page,
    PageTranslation,
    POITranslation,
)
from .utils.contact_utils import Contactlist

if TYPE_CHECKING:
    from django.db.models.base import ModelBase
    from django.db.models.query import QuerySet


class ActiveLanguageContactlist(Contactlist):
    """
    Base class for content translation contact lists
    """

    html_fields: list[str] = ["content"]

    @classmethod
    def filter_callable(cls, objects: QuerySet) -> QuerySet:
        """
        Get only translations in active languages

        :param objects: Objects to be filtered
        :return: Objects that passed the filter
        """
        # Because of large overhead, we only want this filter during the findcontacts management command.
        if settings.FINDCONTACTS_COMMAND_RUNNING:
            # Exclude contacts in inactive languages
            objects = objects.annotate(
                active=Exists(
                    LanguageTreeNode.objects.filter(
                        region=OuterRef(f"{objects.model.foreign_field()}__region"),
                        language=OuterRef("language"),
                        active=True,
                    )
                )
            ).filter(active=True)

        return objects


class PageTranslationContactlist(ActiveLanguageContactlist):
    """
    Class for selecting the PageTranslation model for contact checks
    """

    model: ModelBase = PageTranslation

    @classmethod
    def filter_callable(cls, objects: QuerySet) -> QuerySet:
        """
        Get only latest versions for non-archived pages in active languages

        :param objects: Objects to be filtered
        :return: Objects that passed the filter
        """
        # Apply filter of parent class
        objects = super().filter_callable(objects)
        # Because of large overhead, we only want this filter during the findcontacts management command.
        if settings.FINDCONTACTS_COMMAND_RUNNING:
            # Exclude archived pages
            pages = Page.objects.all().cache_tree(archived=False)
            objects = objects.filter(page__in=pages)

        return objects.distinct("page__pk", "language__pk")


class ImprintTranslationContactlist(ActiveLanguageContactlist):
    """
    Class for selecting the ImprintPageTranslation model for contactchecks
    """

    model: ModelBase = ImprintPageTranslation


class NonArchivedContactList(ActiveLanguageContactlist):
    """
    Class for excluding archived events and locations
    """

    @classmethod
    def filter_callable(cls, objects: QuerySet) -> QuerySet:
        """
        Get only latest translations for non-archived events/locations in active languages

        :param objects: Objects to be filtered
        :return: Objects that passed the filter
        """
        # Apply filter of parent class
        objects = super().filter_callable(objects)
        # Exclude archived events/locations
        objects = objects.filter(
            **{f"{objects.model.foreign_field()}__archived": False}
        ).distinct(f"{objects.model.foreign_field()}__pk", "language__pk")

        return objects


class EventTranslationContactlist(NonArchivedContactList):
    """
    Class for selecting the EventTranslation model for contact checks
    """

    model: ModelBase = EventTranslation

    @classmethod
    def filter_callable(cls, objects: QuerySet) -> QuerySet:
        """
        Get only translations of upcoming events in active languages

        :param objects: Objects to be filtered
        :return: Objects that passed the filter
        """
        # Apply filter of parent class
        objects = super().filter_callable(objects)
        # Exclude past events
        upcoming_events = Event.objects.filter_upcoming()
        objects = objects.filter(event__in=upcoming_events)

        return objects


class POITranslationContactlist(NonArchivedContactList):
    """
    Class for selecting the POITranslation model for contact checks
    """

    model: ModelBase = POITranslation


contactlists = {
    "PageTranslations": PageTranslationContactlist,
    "EventTranslations": EventTranslationContactlist,
    "POITranslations": POITranslationContactlist,
    "ImprintPageTranslations": ImprintTranslationContactlist,
}

# Add a reference to the linklist in the model
for lst in contactlists.values():
    setattr(lst.model, "_contactlist", lst)
