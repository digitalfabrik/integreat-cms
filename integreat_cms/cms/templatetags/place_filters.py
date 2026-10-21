"""
This is a collection of tags and filters for places (:class:`~integreat_cms.cms.models.places.place.Place`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django import template
from django.template.loader import render_to_string
from django.utils.html import escape

if TYPE_CHECKING:
    from django.utils.safestring import SafeString

    from ..models import Language, Place

register = template.Library()


@register.filter
def place_translation_title(place: Place, language: Language) -> str:
    """
    This tag returns the title of the most recent translation of the requested place in the requested language.

    :param place: The requested place
    :param language: The requested language
    :return: The title of the requested translation
    """
    all_place_translations = place.translations
    place_translation = all_place_translations.filter(language__slug=language.slug)
    if place_translation.exists():
        return place_translation.first().title
    if all_place_translations.exists():
        place_translation = all_place_translations.first()
        return f"{place_translation.title} ({place_translation.language})"
    return ""


@register.simple_tag
def render_place_address(place: Place) -> SafeString:
    """
    This tag returns encoded html for the place address container of this place

    :param place: The requested place
    :return: An encoded html string
    """
    return escape(
        render_to_string(
            "ajax_place_form/_place_address_container.html",
            {"place": place, "disabled": False},
        ),
    )
