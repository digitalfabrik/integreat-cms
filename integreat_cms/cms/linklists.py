from linkcheck import Linklist

from .models import PageTranslation, EventTranslation, POITranslation


class ContentTranslationLinklist(Linklist):
    """
    Base class for content translation link lists
    """

    html_fields = ["content"]

    @classmethod
    def filter_callable(cls, objects):
        """
        Get only latest versions for same page and language

        :param objects: Objects to be filtered
        :type objects: ~django.db.models.query.QuerySet
        :return: Objects that passed the filter
        :rtype: ~django.db.models.query.QuerySet
        """
        return objects.distinct(objects.model.foreign_field(), "language")


class PageTranslationLinklist(ContentTranslationLinklist):
    """
    Class for selecting the PageTranslation model for link checks
    """

    model = PageTranslation


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
