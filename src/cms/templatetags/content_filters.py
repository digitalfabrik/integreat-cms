"""
This is a collection of tags and filters which are useful for all content types (:class:`~cms.models.pages.page.Page`,
:class:`~cms.models.events.event.Event` and :class:`~cms.models.pois.poi.POI`).
"""
import logging

from django import template

from ..models import Language

logger = logging.getLogger(__name__)
register = template.Library()


@register.simple_tag
def get_translation(instance, language_code):
    """
    This tag returns the most recent translation of the requested content object in the requested language.

    :param instance: The content object instance
    :type instance: ~cms.models.pages.page.Page, ~cms.models.events.event.Event or ~cms.models.pois.poi.POI

    :param language_code: The code of the requested language
    :type language_code: str

    :return: The translation object of the requested instance
    :rtype: ~cms.models.pages.page_translation.PageTranslation, ~cms.models.events.event_translation.EventTranslation,
            or ~cms.models.pois.poi_translation.POITranslation
    """
    return instance.translations.filter(language__code=language_code).first()


@register.simple_tag
def translated_language_name(language_code):
    """
    This tag returns the name of the requested language in the current backend language

    :param language_code: The code of the requested language
    :type language_code: str

    :return: The translated name of the requested language
    :rtype: str
    """
    language = Language.objects.filter(code=language_code)
    if language.exists():
        return language.first().translated_name
    return ""


@register.simple_tag
def get_language(language_code):
    """
    This tag returns the name of the requested language in the current backend language

    :param language_code: The code of the requested language
    :type language_code: str

    :return: The translated name of the requested language
    :rtype: str
    """
    return Language.objects.filter(code=language_code).first()


# Unify the language codes of backend and content languages
@register.simple_tag
def unify_language_code(language_code):
    """
    This tag returns the unified language code.
    This is used to treat British English and American English as the same language.

    :param language_code: The code of the requested language
    :type language_code: str

    :return: The unified code of the requested language
    :rtype: str
    """
    if language_code == "en-gb":
        return "en-us"
    return language_code


@register.filter
def get_int_list(data, list_name):
    """
    This filter returns the list data of a one-to-many field as ints.

    :param data: The requested form data
    :type data: ~django.http.QueryDict

    :param list_name: The name of the requested field
    :type list_name: str

    :return: The int value list
    :rtype: list [ int ]
    """
    return [int(item) for item in data.getlist(list_name)]


@register.filter
def is_empty(iterable):
    """
    This filter checks whether the given iterable is empty.

    :param iterable: The requested iterable
    :type iterable: ~collections.abc.Iterable

    :return: Whether or not the given iterable is empty
    :rtype: bool
    """
    return not bool(iterable)
