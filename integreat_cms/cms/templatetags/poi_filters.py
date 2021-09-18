"""
This is a collection of tags and filters for points of interest (:class:`~integreat_cms.cms.models.pois.poi.POI`).
"""
from django import template

register = template.Library()


@register.filter
def poi_translation_title(poi, language):
    """
    This tag returns the title of the most recent translation of the requested point of interest in the requested language.

    :param poi: The requested point of interest
    :type poi: ~integreat_cms.cms.models.pois.poi.POI

    :param language: The requested language
    :type language: ~integreat_cms.cms.models.languages.language.Language

    :return: The title of the requested translation
    :rtype: str
    """
    all_poi_translations = poi.translations
    poi_translation = all_poi_translations.filter(language__slug=language.slug)
    if poi_translation.exists():
        return poi_translation.first().title
    if all_poi_translations.exists():
        poi_translation = all_poi_translations.first()
        return f"{poi_translation.title} ({poi_translation.language})"
    return ""
