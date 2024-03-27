from __future__ import annotations

from html import unescape
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any
    from django.db.models.base import ModelBase

from django.utils.html import strip_tags

from integreat_cms.cms.models import (
    EventTranslation,
    Language,
    PageTranslation,
    POITranslation,
)


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
    word_count = 0
    for translation in translations:
        attr_to_count = [translation.title, translation.content]
        if isinstance(translation, POITranslation):
            # Currently only POI translations have a meta_description
            attr_to_count.append(translation.meta_description)
        content_to_count_list = [
            unescape(strip_tags(attr)) for attr in attr_to_count if attr
        ]
        content_to_count = " ".join(content_to_count_list)
        for char in "-;:,;!?\n":
            content_to_count = content_to_count.replace(char, " ")
        word_count += len(content_to_count.split())
    return word_count


def get_english_name(slug: str) -> str:
    """
    return the english name of language

    :param slug: language slug
    :return: english name of the language
    """
    return Language.objects.filter(slug=slug).first().english_name
