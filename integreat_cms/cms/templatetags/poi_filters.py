"""
This is a collection of tags and filters for points of interest (:class:`~integreat_cms.cms.models.pois.poi.POI`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django import template

if TYPE_CHECKING:
    from ..models import Language, POI

register = template.Library()


@register.filter
def poi_translation_title(poi: POI, language: Language) -> str:
    """
    This tag returns the title of the most recent translation of the requested point of interest in the requested language.

    :param poi: The requested point of interest
    :param language: The requested language
    :return: The title of the requested translation
    """
    all_poi_translations = poi.translations
    poi_translation = all_poi_translations.filter(language__slug=language.slug)
    if poi_translation.exists():
        return poi_translation.first().title
    if all_poi_translations.exists():
        poi_translation = all_poi_translations.first()
        return f"{poi_translation.title} ({poi_translation.language})"
    return ""
