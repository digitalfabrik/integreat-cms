"""
This is a collection of tags and filters which are useful for all content types (:class:`~integreat_cms.cms.models.pages.page.Page`,
:class:`~integreat_cms.cms.models.events.event.Event` and :class:`~integreat_cms.cms.models.pois.poi.POI`).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django import template
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from ..constants import translation_status
from ..models import (
    EventTranslation,
    ImprintPageTranslation,
    Language,
    PageTranslation,
    POITranslation,
)

if TYPE_CHECKING:
    from typing import Any

    from django.http import QueryDict
    from django.utils.datastructures import MultiValueDict
    from django.utils.functional import Promise, SimpleLazyObject
    from django.utils.safestring import SafeString

    from ..forms.custom_content_model_form import CustomContentModelForm
    from ..models import Region
    from ..models.abstract_content_model import AbstractContentModel
    from ..models.abstract_content_translation import AbstractContentTranslation

logger = logging.getLogger(__name__)
register = template.Library()


@register.simple_tag
def get_translation(
    instance: AbstractContentModel, language_slug: str
) -> AbstractContentTranslation | None:
    """
    This tag returns the most recent translation of the requested content object in the requested language.

    :param instance: The content object instance
    :param language_slug: The slug of the requested language
    :return: The translation object of the requested instance
            or ~integreat_cms.cms.models.pois.poi_translation.POITranslation
    """
    return instance.get_translation(language_slug)


@register.simple_tag
def get_public_translation(
    instance: AbstractContentModel, language_slug: str
) -> AbstractContentTranslation | None:
    """
    This tag returns the most recent public translation of the requested content object in the requested language.

    :param instance: The content object instance
    :param language_slug: The slug of the requested language
    :return: The translation object of the requested instance
            or ~integreat_cms.cms.models.pois.poi_translation.POITranslation
    """
    return instance.get_public_translation(language_slug)


@register.simple_tag
def translated_language_name(language_slug: str) -> str:
    """
    This tag returns the name of the requested language in the current backend language

    :param language_slug: The slug of the requested language
    :return: The translated name of the requested language
    """
    language = Language.objects.filter(slug=language_slug)
    if language.exists():
        return language.first().translated_name
    return ""


@register.simple_tag
def get_language(language_slug: str) -> Language | None:
    """
    This tag returns the requested language by slug

    :param language_slug: The slug of the requested language
    :return: The requested language
    """
    return Language.objects.filter(slug=language_slug).first()


@register.simple_tag
def minor_edit_label(region: Region, language: Language) -> Promise:
    """
    This tag returns the label of the minor edit field of the given form

    :param region: current region
    :param language: The current language
    :return: The minor edit label
    """
    language_node = region.language_node_by_slug[language.slug]
    if language_node.is_leaf():
        return _("Implications on the translation status")
    return _("Implications on translations")


@register.simple_tag
def minor_edit_help_text(
    region: Region, language: Language, translation_form: CustomContentModelForm
) -> Promise:
    """
    This tag returns the help text of the minor edit field of the given form

    :param region: current region
    :param language: The current language
    :param translation_form: The given model form
    :return: The minor edit help text
    """
    language_node = region.language_node_by_slug[language.slug]
    if language_node.is_leaf():
        return _("Tick if this edit should not change the status of this translation.")
    if language_node.is_root():
        return translation_form["minor_edit"].help_text
    return _(
        "Tick if this edit should not change the status of this translation and does not require an update of translations in other languages."
    )


@register.simple_tag
def build_url(
    target: SafeString,
    region_slug: str,
    language_slug: str,
    content_field: SafeString | str | None = None,
    content_id: int | None = None,
) -> str:
    """
    This tag returns the requested language by slug

    :param target: The slug of the requested target
    :param region_slug: The slug of the requested region
    :param language_slug: The slug of the requested language
    :param content_field: The name of the content field
    :param content_id: The id of the content
    :return: list of args
    """
    kwargs: dict[str, str | int] = {
        "region_slug": region_slug,
        "language_slug": language_slug,
    }
    if content_field and content_id:
        kwargs[content_field] = content_id
    return reverse(target, kwargs=kwargs)


@register.filter
def remove(elements: list[Any], element: Any) -> list[Any]:
    """
    This tag removes an element from a list.

    :param elements: The given list of elements
    :param element: The element to be removed
    :return: The list without the element
    """
    try:
        # Copy input list to make sure it is not modified in place
        result = elements.copy()
        result.remove(element)
        return result
    except ValueError:
        # If the element wasn't in the list to begin with, just return the input
        return elements


@register.filter
def sort_translation_states(
    translation_states: dict[str, tuple[Language, str]],
    second_language: Language,
) -> list[tuple[Language, str]]:
    """
    This filter sorts languages in language tabs

    :param translation_states: Other languages
    :param second_language: The current language
    :return: the filtered list with the current language on the second position
    """
    try:
        first_language_slug = next(iter(translation_states))
    except StopIteration:
        return [(second_language, translation_status.MISSING)]
    if first_language_slug != second_language.slug:
        second_language_state = translation_states.pop(second_language.slug)
        translation_states_list = list(translation_states.values())
        translation_states_list.insert(1, second_language_state)
    else:
        translation_states_list = list(translation_states.values())
    return translation_states_list


@register.filter
def get_int_list(data: QueryDict, list_name: str) -> list[int]:
    """
    This filter returns the list data of a one-to-many field as ints.

    :param data: The requested form data
    :param list_name: The name of the requested field
    :return: The int value list
    """
    return [int(item) for item in data.getlist(list_name)]


@register.filter
def is_empty(iterable: MultiValueDict) -> bool:
    """
    This filter checks whether the given iterable is empty.

    :param iterable: The requested iterable
    :return: Whether or not the given iterable is empty
    """
    return not bool(iterable)


@register.simple_tag
def object_translation_has_view_perm(
    user: SimpleLazyObject, obj: AbstractContentTranslation
) -> bool:
    """
    This filter accepts any translation of Event, Page or Poi and returns
    whether this account has the permission to view this object

    :param user: The requested user
    :param obj: The requested object
               ~integreat_cms.cms.models.events.event_translation.EventTranslation, or ~integreat_cms.cms.models.pois.poi_translation.POITranslation

    :raises ValueError: if the object is not a translation of Event, Page or Poi

    :return: Whether this account is allowed to view this object
    """
    if isinstance(obj, EventTranslation):
        return user.has_perm("cms.view_event")
    if isinstance(obj, PageTranslation):
        return user.has_perm("cms.view_page")
    if isinstance(obj, POITranslation):
        return user.has_perm("cms.view_poi")
    if isinstance(obj, ImprintPageTranslation):
        return user.has_perm("cms.view_imprint")
    raise ValueError(f"Invalid model: {type(obj)}")
