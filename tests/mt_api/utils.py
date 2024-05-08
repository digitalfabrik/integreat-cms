from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any
    from django.db.models.base import ModelBase

from integreat_cms.cms.models import (
    EventTranslation,
    Language,
    PageTranslation,
    POITranslation,
)
from integreat_cms.core.utils.word_count import word_count


def get_content_translations(
    content_model: ModelBase, ids: list[int], *language_slugs: str
) -> list[dict[str, Any]]:
    """
    Load the translations for the given content model from the database

    :param content_model: Name of the requested data model (Page, Event or POI)
    :param ids: List of ids of the requested model entries
    :param language_slugs: List of the requested language slugs
    :return: Content translations
    """
    return [
        {
            "content_entry": content_entry,
            **{slug: content_entry.get_translation(slug) for slug in language_slugs},
        }
        for content_entry in content_model.objects.filter(id__in=ids)
    ]


def get_word_count(
    translations: list[EventTranslation] | (
        list[PageTranslation] | list[POITranslation]
    ),
) -> int:
    """
    Count the total number of words in the title, content and meta-description of translations

    :param translations: List of translations (Pages, Events or POIs)
    :return: Word count
    """
    words = 0
    for translation in translations:
        words += word_count(translation)
    return words


def get_english_name(slug: str) -> str:
    """
    return the english name of language

    :param slug: language slug
    :return: english name of the language
    """
    return Language.objects.filter(slug=slug).first().english_name
