from django.conf import settings

from linkcheck import Linklist

from .models import Page, PageTranslation, EventTranslation, POITranslation


class ContentTranslationLinklist(Linklist):
    """
    Base class for content translation link lists
    """

    html_fields = ["content"]

    @classmethod
    def filter_callable(cls, objects):
        """
        Get only latest versions for non-archived events/locations

        :param objects: Objects to be filtered
        :type objects: ~django.db.models.query.QuerySet

        :return: Objects that passed the filter
        :rtype: ~django.db.models.query.QuerySet
        """
        return objects.filter(
            **{f"{objects.model.foreign_field()}__archived": False}
        ).distinct(f"{objects.model.foreign_field()}__pk", "language__pk")


class PageTranslationLinklist(Linklist):
    """
    Class for selecting the PageTranslation model for link checks
    """

    model = PageTranslation
    html_fields = ["content"]

    @classmethod
    def filter_callable(cls, objects):
        """
        Get only latest versions for non-archived pages

        :param objects: Objects to be filtered
        :type objects: ~django.db.models.query.QuerySet

        :return: Objects that passed the filter
        :rtype: ~django.db.models.query.QuerySet
        """
        # Since filtering the archived pages causes a lot of overhead, we only want this during the findlinks management command.
        if settings.LINKCHECK_EXCLUDE_ARCHIVED_PAGES:
            pages = Page.objects.all().cache_tree(archived=False)
            objects = objects.filter(page__in=pages)
        return objects.distinct("page__pk", "language__pk")


class EventTranslationLinklist(ContentTranslationLinklist):
    """
    Class for selecting the EventTranslation model for link checks
    """

    model = EventTranslation


class POITranslationLinklist(ContentTranslationLinklist):
    """
    Class for selecting the POITranslation model for link checks
    """

    model = POITranslation


linklists = {
    "PageTranslations": PageTranslationLinklist,
    "EventTranslations": EventTranslationLinklist,
    "POITranslations": POITranslationLinklist,
}
