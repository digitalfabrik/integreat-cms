from __future__ import annotations

from html import unescape
from typing import TYPE_CHECKING

from django.utils.html import strip_tags

if TYPE_CHECKING:

    from ...cms.models import EventTranslation, PageTranslation, POITranslation


def word_count(
    translation: EventTranslation | (PageTranslation | POITranslation),
) -> int:
    """
    This function counts the number of words in a content translation
    """
    attributes = [
        getattr(translation, attr, None)
        for attr in ["title", "content", "meta_description"]
    ]

    content_to_translate = [unescape(strip_tags(attr)) for attr in attributes if attr]
    content_to_translate_str = " ".join(content_to_translate)
    for char in "-;:,;!?\n":
        content_to_translate_str = content_to_translate_str.replace(char, " ")

    return len(content_to_translate_str.split())
