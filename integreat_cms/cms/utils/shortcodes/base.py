"""
This module defines what a shortcode is.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, ClassVar

    from lxml.html import HtmlElement


class Shortcode(ABC):
    """
    A marker which references an object from the content of a translation.

    Shortcodes are only resolved when the content is requested, so that it always reflects the
    current state of the referenced object (see
    ``ADR/0001-compose-referenced-objects-into-content-dynamically-shortcodes.md``).

    Every shortcode has an atomic form (``[keyword …]``) and may additionally have a block
    scoped form (``[block_keyword …]…[/block_keyword]``) which encloses content.

    Subclasses become known to the application by being decorated with
    :func:`~integreat_cms.cms.utils.shortcodes.registry.register`.
    """

    #: The keyword of the atomic form, for example ``page`` in ``[page 1]``
    keyword: ClassVar[str]

    #: The keyword of the block scoped form, for example ``page_link`` in
    #: ``[page_link 1]…[/page_link]``, or ``None`` if this shortcode has no block scoped form
    block_keyword: ClassVar[str | None] = None

    @property
    def block_end_keyword(self) -> str | None:
        """
        The keyword which closes the block scoped form of this shortcode

        :return: The end keyword, or ``None`` if this shortcode has no block scoped form
        """
        return f"/{self.block_keyword}" if self.block_keyword else None

    @abstractmethod
    def expand(
        self,
        pargs: list[str],
        kwargs: dict[str, str],
        context: dict[str, Any] | None,
    ) -> str:
        """
        Expand the atomic form of this shortcode into the html which is delivered to end users

        :param pargs: The positional arguments of the shortcode
        :param kwargs: The keyword arguments of the shortcode
        :param context: The context the shortcode is expanded in
        :return: The html which represents the referenced object
        """

    def expand_block(
        self,
        pargs: list[str],
        kwargs: dict[str, str],
        context: dict[str, Any] | None,
        content: str = "",
    ) -> str:
        """
        Expand the block scoped form of this shortcode into the html which is delivered to end users

        :param pargs: The positional arguments of the shortcode
        :param kwargs: The keyword arguments of the shortcode
        :param context: The context the shortcode is expanded in
        :param content: The content enclosed by the shortcode
        :raises NotImplementedError: If this shortcode has no block scoped form
        :return: The html which represents the referenced object
        """
        raise NotImplementedError(
            f"The shortcode {self.keyword!r} has no block scoped form",
        )

    def unparse(self, pargs: list[str], kwargs: dict[str, str]) -> str:
        """
        Rebuild the source representation of the atomic form of this shortcode.

        This is what an expansion falls back to when the referenced object cannot be resolved
        and the shortcode should be kept verbatim instead.

        :param pargs: The positional arguments of the shortcode
        :param kwargs: The keyword arguments of the shortcode
        :return: The shortcode tag
        """
        return _unparse(self.keyword, pargs, kwargs)

    def unparse_block(
        self,
        pargs: list[str],
        kwargs: dict[str, str],
        content: str,
    ) -> str:
        """
        Rebuild the source representation of the block scoped form of this shortcode

        :param pargs: The positional arguments of the shortcode
        :param kwargs: The keyword arguments of the shortcode
        :param content: The content enclosed by the shortcode
        :return: The shortcode with its content
        """
        return (
            _unparse(self.block_keyword or self.keyword, pargs, kwargs)
            + content
            + f"[{self.block_end_keyword}]"
        )


class EditableShortcode(Shortcode, ABC):
    """
    A shortcode which is presented as ordinary html while the content is edited in the CMS.

    Editors should not have to care about shortcodes, so such a shortcode bundles three pieces
    which together let the CMS hide it:

    1. :meth:`expand_for_cms` (and :meth:`expand_block_for_cms`) turn the shortcode into the
       html which is loaded into the editor
    2. :meth:`matches` cheaply decides whether an element might be that html again
    3. :meth:`collapse` resolves what :meth:`matches` found and replaces it by the shortcode

    The split between 2. and 3. exists because every element of every saved content is passed
    through :meth:`matches`, which therefore must not query the database. Only the elements it
    accepts are handed to :meth:`collapse`, which may.
    """

    @abstractmethod
    def expand_for_cms(
        self,
        pargs: list[str],
        kwargs: dict[str, str],
        context: dict[str, Any] | None,
    ) -> str:
        """
        Expand the atomic form of this shortcode into the html which is edited in the CMS

        :param pargs: The positional arguments of the shortcode
        :param kwargs: The keyword arguments of the shortcode
        :param context: The context the shortcode is expanded in
        :return: The html which represents the referenced object
        """

    def expand_block_for_cms(
        self,
        pargs: list[str],
        kwargs: dict[str, str],
        context: dict[str, Any] | None,
        content: str = "",
    ) -> str:
        """
        Expand the block scoped form of this shortcode into the html which is edited in the CMS

        :param pargs: The positional arguments of the shortcode
        :param kwargs: The keyword arguments of the shortcode
        :param context: The context the shortcode is expanded in
        :param content: The content enclosed by the shortcode
        :raises NotImplementedError: If this shortcode has no block scoped form
        :return: The html which represents the referenced object
        """
        raise NotImplementedError(
            f"The shortcode {self.keyword!r} has no block scoped form",
        )

    @abstractmethod
    def matches(self, element: HtmlElement) -> bool:
        """
        Cheaply decide whether ``element`` might be an expansion of this shortcode.

        This is called for every element of every saved content, so it must be a matter of
        string comparisons and must never query the database. False positives are fine,
        :meth:`collapse` sorts them out.

        :param element: The element to check
        :return: Whether the element is a candidate for being collapsed
        """

    @abstractmethod
    def collapse(self, element: HtmlElement) -> bool:
        """
        Replace ``element`` by the shortcode representing it, if it really references an object

        :param element: The element which should be collapsed
        :return: Whether the element was replaced
        """


def _unparse(keyword: str, pargs: list[str], kwargs: dict[str, str]) -> str:
    """
    Rebuild the source representation of a shortcode tag

    :param keyword: The keyword of the shortcode
    :param pargs: The positional arguments of the shortcode
    :param kwargs: The keyword arguments of the shortcode
    :return: The shortcode tag
    """
    # Everything but the id of the target is quoted, so that no quotes get lost while a
    # shortcode which cannot be resolved is kept verbatim
    arguments = [
        parg if index == 0 and parg and not any(map(str.isspace, parg)) else f'"{parg}"'
        for index, parg in enumerate(pargs)
    ]
    arguments += [f'{key}="{value}"' for key, value in kwargs.items()]
    return f"[{' '.join([keyword, *arguments])}]"
