"""
This module contains the shortcode which references a :class:`~integreat_cms.cms.models.pages.page.Page`
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...models import Page
from .internal_link import InternalLinkShortcode
from .registry import register

if TYPE_CHECKING:
    from typing import Final

#: The first path segment of webapp urls which point to something else than a page
NON_PAGE_URL_INFIXES: Final[frozenset[str]] = frozenset(
    {"events", "locations", "disclaimer", "news", "offers", "search"},
)


@register
class PageShortcode(InternalLinkShortcode):
    """
    Shortcode to insert an internal link to a :class:`~integreat_cms.cms.models.pages.page.Page`.

    Positional arguments of the atomic form ``[page …]``:

    * ``page_id``              – The id of the :class:`~integreat_cms.cms.models.pages.page.Page` to which should be linked
    * ``link_text`` (optional) – If not given, the title of the public :class:`~integreat_cms.cms.models.pages.page_translation.PageTranslation` is used

    If the target page has an icon set and the shortcode has no ``link_text``,
    the icon will be included as an ``<img>`` before the page title.

    Whenever the link should wrap html instead of plain text, the block scoped form
    ``[page_link …]…[/page_link]`` is used, which takes only the ``page_id``.

    .. list-table:: Examples
        :widths: 45 55
        :header-rows: 0

        * - ``[page 1]``
          - ``<a href="https://integreat.app/augsburg/de/willkommen/">Willkommen</a>``
        * - ``[page 1 "this page"]``
          - ``<a href="https://integreat.app/augsburg/de/willkommen/">this page</a>``
        * - ``[page_link 1]<b>hier</b>[/page_link]``
          - ``<a href="https://integreat.app/augsburg/de/willkommen/"><b>hier</b></a>``
        * - ``[page 999999]``
          - ``<i>[MISSING LINK]</i>``
        * - ``[page_link 999999]<b>hier</b>[/page_link]``
          - ``<i>[<b>hier</b>]</i>``
    """

    keyword = "page"
    block_keyword = "page_link"
    model = Page
    short_url_infix = "p"

    def matches_url_infix(self, infix: str) -> bool:
        """
        Pages are the only content whose urls have no distinguishing path segment, so every
        url which does not belong to another kind of content points to a page

        :param infix: The first path segment after region and language
        :return: Whether a url with this segment points to a page
        """
        return infix not in NON_PAGE_URL_INFIXES
