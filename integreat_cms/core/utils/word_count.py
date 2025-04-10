from __future__ import annotations

from html import unescape

from django.utils.html import strip_tags


def word_count(
    attributes_to_translate: list[tuple[str, str]],
) -> int:
    """
    This function counts the number of words in a content translation
    """
    if not attributes_to_translate:
        return 0

    content_to_translate = [
        unescape(strip_tags(attr)) for (_, attr) in attributes_to_translate
    ]
    content_to_translate_str = " ".join(content_to_translate)
    for char in "-;:,;!?\n":
        content_to_translate_str = content_to_translate_str.replace(char, " ")

    return len(content_to_translate_str.split())
