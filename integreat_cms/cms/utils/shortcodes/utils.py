from collections.abc import Callable
from typing import ParamSpec, TypeVar

import shortcodes

R = TypeVar("R")
P = ParamSpec("P")


def shortcode(
    func: Callable[P, R], tag: str | None = None, endtag: str | None = None
) -> Callable[P, R]:
    """Decorator to register a function as a shortcode"""
    if tag is None:
        tag = func.__name__
    shortcodes.register(tag, endtag)(func)
    return func
