"""
This module keeps the registry of all known shortcodes.
"""

from __future__ import annotations

from functools import cache
from typing import TYPE_CHECKING

from .base import EditableShortcode

if TYPE_CHECKING:
    from .base import Shortcode


#: All registered shortcodes, in the order they were registered
_registry: list[Shortcode] = []


def register[ShortcodeT: Shortcode](shortcode: type[ShortcodeT]) -> type[ShortcodeT]:
    """
    Class decorator which makes a shortcode known to the application::

        @register
        class CatShortcode(Shortcode):
            keyword = "cat"

            def expand(self, pargs, kwargs, context):
                return "(=^･ω･^=)"

    :param shortcode: The shortcode to register
    :return: The shortcode itself, so that this can be used as a decorator
    """
    _registry.append(shortcode())
    return shortcode


@cache
def get_shortcodes() -> tuple[Shortcode, ...]:
    """
    Get all registered shortcodes.

    The modules which define them are imported here instead of at the top of this module,
    because a shortcode may need anything from the models to the content utils, which in turn
    need this package to collapse content into shortcodes.

    :return: The registered shortcodes
    """
    from . import contact, page  # noqa: F401

    return tuple(_registry)


@cache
def editable_shortcodes() -> tuple[EditableShortcode, ...]:
    """
    Get the shortcodes which are hidden from the users of the CMS

    :return: The editable shortcodes
    """
    return tuple(
        shortcode
        for shortcode in get_shortcodes()
        if isinstance(shortcode, EditableShortcode)
    )
