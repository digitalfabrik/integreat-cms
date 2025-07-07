"""
This module contains implementations for the shortcodes content filters
"""

from typing import Any

import shortcodes
from django import template
from django.template.defaultfilters import stringfilter

from .contact import contact
from .page import page

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
    except shortcodes.ShortcodeError:
        # We failed expanding the shortcodes,
        # the best way we can fail gracefully is to just return the original content
        return content
