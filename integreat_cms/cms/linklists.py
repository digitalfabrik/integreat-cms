from django.conf import settings
from django.db.models import Exists, OuterRef
from linkcheck import Linklist

from .models import (
    Event,
    EventTranslation,
    LanguageTreeNode,
    Page,
    PageTranslation,
    POITranslation,
)


class ActiveLanguageLinklist(Linklist):
    """
    Base class for content translation link lists
    """

    html_fields = ["content"]

    @classmethod
    def filter_callable(cls, objects):
        """
        Get only translations in active languages

        :param objects: Objects to be filtered
        :type objects: ~django.db.models.query.QuerySet

        :return: Objects that passed the filter
        :rtype: ~django.db.models.query.QuerySet
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
                    )
                )
            ).filter(active=True)

        return objects


class PageTranslationLinklist(ActiveLanguageLinklist):
    """
    Class for selecting the PageTranslation model for link checks
    """

    model = PageTranslation

    @classmethod
    def filter_callable(cls, objects):
        """
        Get only latest versions for non-archived pages in active languages

        :param objects: Objects to be filtered
        :type objects: ~django.db.models.query.QuerySet

        :return: Objects that passed the filter
        :rtype: ~django.db.models.query.QuerySet
        """
        # Apply filter of parent class
        objects = super().filter_callable(objects)
        # Because of large overhead, we only want this filter during the findlinks management command.
        if settings.LINKCHECK_COMMAND_RUNNING:
            # Exclude archived pages
            pages = Page.objects.all().cache_tree(archived=False)
            objects = objects.filter(page__in=pages)

        return objects.distinct("page__pk", "language__pk")


class NonArchivedLinkList(ActiveLanguageLinklist):
    """
    Class for excluding archived events and locations
    """

    @classmethod
    def filter_callable(cls, objects):
        """
        Get only latest translations for non-archived events/locations in acitive languages

        :param objects: Objects to be filtered
        :type objects: ~django.db.models.query.QuerySet

        :return: Objects that passed the filter
        :rtype: ~django.db.models.query.QuerySet
        """
        # Apply filter of parent class
        objects = super().filter_callable(objects)
        # Exclude archived events/locations
        objects = objects.filter(
            **{f"{objects.model.foreign_field()}__archived": False}
        ).distinct(f"{objects.model.foreign_field()}__pk", "language__pk")

        return objects


class EventTranslationLinklist(NonArchivedLinkList):
    """
    Class for selecting the EventTranslation model for link checks
    """

    model = EventTranslation

    @classmethod
    def filter_callable(cls, objects):
        """
        Get only translations of upcoming events in active languages

        :param objects: Objects to be filtered
        :type objects: ~django.db.models.query.QuerySet

        :return: Objects that passed the filter
        :rtype: ~django.db.models.query.QuerySet
        """
        # Apply filter of parent class
        objects = super().filter_callable(objects)
        # Exclude past events
        upcoming_events = Event.objects.filter_upcoming()
        objects = objects.filter(event__in=upcoming_events)

        return objects


class POITranslationLinklist(NonArchivedLinkList):
    """
    Class for selecting the POITranslation model for link checks
    """

    model = POITranslation


linklists = {
    "PageTranslations": PageTranslationLinklist,
    "EventTranslations": EventTranslationLinklist,
    "POITranslations": POITranslationLinklist,
}
