from __future__ import annotations

from typing import Any, TYPE_CHECKING

from django.conf import settings
from django.db.models import Exists, OuterRef
from linkcheck import Linklist

from .models import (
    Event,
    EventTranslation,
    ImprintPageTranslation,
    LanguageTreeNode,
    Organization,
    Page,
    PageTranslation,
    POITranslation,
)

if TYPE_CHECKING:
    from django.db.models.base import ModelBase
    from django.db.models.query import QuerySet


import linkcheck.listeners

from integreat_cms.core.management.commands.loaddata import post_loaddata, pre_loaddata
from integreat_cms.core.management.commands.migrate import (
    post_full_migration,
    pre_full_migration,
)


def set_linkcheck_immediate(sender: Any, **kwargs: dict[str, Any]) -> None:  # noqa: ARG001
    # Make linkcheck run inline instead of a background thread to see if CI problems magically resolve itself
    linkcheck.listeners.tests_running = True


def set_linkcheck_in_background(sender: Any, **kwargs: dict[str, Any]) -> None:  # noqa: ARG001
    # Revert to the default behaviour of running linkcheck in the background
    linkcheck.listeners.tests_running = False


pre_full_migration.connect(set_linkcheck_in_background)
post_full_migration.connect(set_linkcheck_immediate)

pre_loaddata.connect(set_linkcheck_in_background)
post_loaddata.connect(set_linkcheck_immediate)

set_linkcheck_immediate(__name__)


class ActiveLanguageLinklist(Linklist):
    """
    Base class for content translation link lists
    """

    html_fields: list[str] = ["content"]

    @classmethod
    def filter_callable(cls, objects: QuerySet) -> QuerySet:
        """
        Get only translations in active languages

        :param objects: Objects to be filtered
        :return: Objects that passed the filter
        """
        # Because of large overhead, we only want this filter during the findlinks management command.
        if settings.LINKCHECK_COMMAND_RUNNING:
            # Exclude links in inactive languages
            objects = objects.annotate(
                active=Exists(
                    LanguageTreeNode.objects.filter(
                        region=OuterRef(f"{objects.model.foreign_field()}__region"),
                        language=OuterRef("language"),
                        active=True,
                    ),
                ),
            ).filter(active=True)

        return objects


class PageTranslationLinklist(ActiveLanguageLinklist):
    """
    Class for selecting the PageTranslation model for link checks
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
        # Because of large overhead, we only want this filter during the findlinks management command.
        if settings.LINKCHECK_COMMAND_RUNNING:
            # Exclude archived pages
            pages = Page.objects.all().cache_tree(archived=False)
            objects = objects.filter(page__in=pages)

        return objects.distinct("page__pk", "language__pk")


class ImprintTranslationLinklist(ActiveLanguageLinklist):
    """
    Class for selecting the ImprintPageTranslation model for linkchecks
    """

    model: ModelBase = ImprintPageTranslation


class NonArchivedLinkList(ActiveLanguageLinklist):
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
        return objects.filter(
            **{f"{objects.model.foreign_field()}__archived": False},
        ).distinct(f"{objects.model.foreign_field()}__pk", "language__pk")


class EventTranslationLinklist(NonArchivedLinkList):
    """
    Class for selecting the EventTranslation model for link checks
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
        return objects.filter(event__in=upcoming_events)


class POITranslationLinklist(NonArchivedLinkList):
    """
    Class for selecting the POITranslation model for link checks
    """

    model: ModelBase = POITranslation


class OrganizationLinklist(Linklist):
    """
    Class for selecting the Organization model for link checks
    """

    model: ModelBase = Organization

    url_fields = ["website"]


linklists = {
    "PageTranslations": PageTranslationLinklist,
    "EventTranslations": EventTranslationLinklist,
    "POITranslations": POITranslationLinklist,
    "ImprintPageTranslations": ImprintTranslationLinklist,
    "Organizations": OrganizationLinklist,
}
