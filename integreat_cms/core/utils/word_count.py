from __future__ import annotations

from html import unescape

from django.utils.html import strip_tags

from ...cms.models.abstract_content_translation import AbstractContentTranslation


def word_count(
    translation: str | AbstractContentTranslation,
) -> int:
    """
    This function counts the number of words in a content translation
    """
    if isinstance(translation, AbstractContentTranslation):
        attributes = [
            getattr(translation, attr, None)
            for attr in ["title", "content", "meta_description"]
        ]

        content_to_translate = [
            unescape(strip_tags(attr)) for attr in attributes if attr
        ]
        content_to_translate_str = " ".join(content_to_translate)
    else:
        content_to_translate_str = translation

    for char in "-;:,;!?\n":
        content_to_translate_str = content_to_translate_str.replace(char, " ")

    return len(content_to_translate_str.split())
