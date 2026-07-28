"""
This module contains implementations for the shortcodes content filters
"""

from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

import shortcodes
from django import template
from django.template.defaultfilters import stringfilter

from .contact import contact
from .page import page, page_link

if TYPE_CHECKING:
    from ...models.abstract_content_translation import AbstractContentTranslation

logger = logging.getLogger(__name__)

register = template.Library()

# Needed context:
# - region
# - language
# - accessed path?
# - login status?
parser = shortcodes.Parser(start="[", end="]", esc="\\", ignore_unknown=True)


@register.filter
@stringfilter
def expand_shortcodes(content: str, context: dict[str, Any] | None = None) -> str:
    try:
        return parser.parse(content, context)
    except shortcodes.ShortcodeError as e:
        logger.warning(
            "Failed expanding shortcodes:  %s\ncontext: %r", e, context, exc_info=True
        )
        # We failed expanding the shortcodes,
        # the best way we can fail gracefully is to just return the original content
        return content


def expand_shortcodes_of(translation: AbstractContentTranslation) -> str:
    """
    Expand all shortcodes in the content of a content translation

    :param translation: The translation whose content should be expanded
    :return: The expanded content
    """
    return expand_shortcodes(
        translation.content,
        context={
            "region_slug": translation.foreign_object.region.slug,
            "language_slug": translation.language.slug,
            "content_object": translation,
        },
    )
