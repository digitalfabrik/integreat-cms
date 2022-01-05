"""
This is a collection of tags and filters which are useful for all content types (:class:`~integreat_cms.cms.models.pages.page.Page`,
:class:`~integreat_cms.cms.models.events.event.Event` and :class:`~integreat_cms.cms.models.pois.poi.POI`).
"""
import logging

from django.urls import reverse

from django import template

from ..models import Language, PageTranslation, EventTranslation, POITranslation

logger = logging.getLogger(__name__)
register = template.Library()


@register.simple_tag
def get_translation(instance, language_slug):
    """
    This tag returns the most recent translation of the requested content object in the requested language.

    :param instance: The content object instance
    :type instance: ~integreat_cms.cms.models.pages.page.Page, ~integreat_cms.cms.models.events.event.Event or ~integreat_cms.cms.models.pois.poi.POI

    :param language_slug: The slug of the requested language
    :type language_slug: str

    :return: The translation object of the requested instance
    :rtype: ~integreat_cms.cms.models.pages.page_translation.PageTranslation, ~integreat_cms.cms.models.events.event_translation.EventTranslation,
            or ~integreat_cms.cms.models.pois.poi_translation.POITranslation
    """
    return instance.get_translation(language_slug)


@register.simple_tag
def get_public_translation(instance, language_slug):
    """
    This tag returns the most recent public translation of the requested content object in the requested language.

    :param instance: The content object instance
    :type instance: ~integreat_cms.cms.models.pages.page.Page, ~integreat_cms.cms.models.events.event.Event or ~integreat_cms.cms.models.pois.poi.POI

    :param language_slug: The slug of the requested language
    :type language_slug: str

    :return: The translation object of the requested instance
    :rtype: ~integreat_cms.cms.models.pages.page_translation.PageTranslation, ~integreat_cms.cms.models.events.event_translation.EventTranslation,
            or ~integreat_cms.cms.models.pois.poi_translation.POITranslation
    """
    return instance.get_public_translation(language_slug)


@register.simple_tag
def translated_language_name(language_slug):
    """
    This tag returns the name of the requested language in the current backend language

    :param language_slug: The slug of the requested language
    :type language_slug: str

    :return: The translated name of the requested language
    :rtype: str
    """
    language = Language.objects.filter(slug=language_slug)
    if language.exists():
        return language.first().translated_name
    return ""


@register.simple_tag
def get_language(language_slug):
    """
    This tag returns the requested language by slug

    :param language_slug: The slug of the requested language
    :type language_slug: str

    :return: The requested language
    :rtype: ~integreat_cms.cms.models.languages.language.Language
    """
    return Language.objects.filter(slug=language_slug).first()


@register.simple_tag
def build_url(target, region_slug, language_slug, content_field, content_id):
    """
    This tag returns the requested language by slug

    :param target: The slug of the requested target
    :type target: str

    :param region_slug: The slug of the requested region
    :type region_slug: str

    :param language_slug: The slug of the requested language
    :type language_slug: str

    :param content_field: The name of the content field
    :type content_field: str

    :param content_id: The id of the content
    :type content_id: int

    :return: list of args
    :rtype: str
    """
    return reverse(
        target,
        kwargs={
            "region_slug": region_slug,
            "language_slug": language_slug,
            content_field: content_id,
        },
    )


@register.filter
def remove(queryset, instance):
    """
    This tag removes an object instance from a QuerySet.

    :param queryset: The given QuerySet
    :type queryset: ~django.db.models.query.QuerySet

    :param instance: The object instance to be removed
    :type instance: object

    :return: The QuerySet without the object instance
    :rtype: ~django.db.models.query.QuerySet
    """
    return queryset.exclude(id=instance.id)


@register.filter
def sort_languages(other_languages, current_language):
    """
    This filter sorts languages in language tabs

    :param current_language: The current language
    :type current_language: ~integreat_cms.cms.models.languages.language.Language

    :param other_languages: Other languages
    :type other_languages: ~django.db.models.query.QuerySet [ ~integreat_cms.cms.models.languages.language.Language ]

    :return: the filtered list with the current language on the second position
    :rtype: list
    """
    other_languages = list(other_languages)
    if other_languages[0] != current_language:
        other_languages.remove(current_language)
        other_languages.insert(1, current_language)

    return other_languages


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


@register.simple_tag
def object_translation_has_view_perm(user, obj):
    """
    This filter accepts any translation of Event, Page or Poi and returns
    whether the user has the permission to view this object

    :param user: The requested user
    :type user: ~integreat_cms.cms.models.users.user.User

    :param obj: The requested object
    :type obj: ~integreat_cms.cms.models.pages.page_translation.PageTranslation,
               ~integreat_cms.cms.models.events.event_translation.EventTranslation, or ~integreat_cms.cms.models.pois.poi_translation.POITranslation

    :raises ValueError: if the object is not a translation of Event, Page or Poi

    :return: Whether the user is allowed to view this object
    :rtype: bool
    """
    if isinstance(obj, EventTranslation):
        return user.has_perm("cms.view_event")
    if isinstance(obj, PageTranslation):
        return user.has_perm("cms.view_page")
    if isinstance(obj, POITranslation):
        return user.has_perm("cms.view_poi")
    raise ValueError(f"Invalid model: {type(obj)}")
