from collections.abc import Callable
from typing import ParamSpec, TypeVar

import shortcodes

R = TypeVar("R")
P = ParamSpec("P")


def shortcode(
    tag: Callable[P, R] | str | None, endtag: str | None = None
) -> Callable[[Callable[P, R]], Callable[P, R]] | Callable[P, R]:
    """
    Decorator to register a function as a shortcode

    For example, this would declare a shortcode ``cat`` (taken from the function name),
    where the first parameter can be ``0`` or ``1`` to select between two ASCII cats to insert::

        @shortcode
        def cat(pargs, kwargs, context, content=""):
            cats = '''
                (=^･ω･^=)
                ฅ/ᐠ- ˕ -マ
            '''.split()
            return cats[pargs[0]]

    If the shortcode should use a different keyword than just the name of the function,
    it can be provided as an argument to the decorator::

        @shortcode("ASCII_cat")
        def cat(pargs, kwargs, context, content=""):
        […]

    When ``endtag`` is given, the shortcode will not be atomic but can enclose content
    between its opening tag and end tag::

        @shortcode("cat", "tac")
        def cat(pargs, kwargs, context, content=""):
            return f"⚞({content})⚟"

    This can then be used as ``[cat]some <b>feline content</b>[tac]``.
    """

    def inner(func: Callable[P, R]) -> Callable[P, R]:
        """Just register the shortcode once and return the original function"""
        nonlocal tag
        if not tag:
            # Default tag is the function name
            tag = func.__name__
        shortcodes.register(tag, endtag)(func)
        return func

    if callable(tag):
        # We are being used without parantheses (``@shortcode``)
        # and the first argument already is the function being decorated.
        func = tag
        tag = None
        return inner(func)
    # We are being used with parantheses (``@shortcode("keyword")``).
    # Return the inner function itself so it can be called with the function being defined next
    return inner
