"""
This module contains implementations for the shortcodes content filters
"""

import logging
from typing import Any

import shortcodes
from django import template
from django.template.defaultfilters import stringfilter

from .contact import contact
from .page import page


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
        n = "\n"
        logger.warning(f"Failed expanding shortcodes:  {e}{n}context: {context!r}", exc_info=True)
        # We failed expanding the shortcodes,
        # the best way we can fail gracefully is to just return the original content
        return content
