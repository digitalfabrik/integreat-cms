from copy import deepcopy
from typing import Any

from django.utils.translation import gettext_lazy as _
from lxml.etree import LxmlError
from lxml.html import Element, fromstring, tostring

from ...models import Page, PageTranslation
from ..content_utils import hide_anchor_tag_around_single_image
from ..link_shortcode_utils import (
    PAGE_KEYWORD,
    PAGE_LINK_END_KEYWORD,
    PAGE_LINK_KEYWORD,
)
from .utils import shortcode


def _get_public_translation(
    page_id: str | None,
    context: dict[str, Any] | None,
) -> PageTranslation:
    """
    Get the public translation a page shortcode refers to

    :param page_id: The id of the :class:`~integreat_cms.cms.models.pages.page.Page` to which should be linked
    :param context: The context the shortcode is expanded in
    :raises ~integreat_cms.cms.models.pages.page.Page.DoesNotExist: If the page does not exist
    :raises ~integreat_cms.cms.models.pages.page_translation.PageTranslation.DoesNotExist: If the
        page has no public translation in the requested language
    :return: The public translation which is linked to
    """
    page = Page.objects.get(id=page_id)
    translation = page.get_public_translation(
        (context or {}).get("language_slug", page.region.default_language.slug),
    )
    if translation is None:
        raise PageTranslation.DoesNotExist
    return translation


def _missing_link(inner_html: str) -> Element:
    """
    Build the replacement for a page shortcode whose target cannot be resolved

    :param inner_html: The content of the link, if it has any
    :return: The element to insert instead of the link
    """
    TEXT_MISSING = _(
        "MISSING LINK"
    )  # Separate variable because gettext apparently does not find _() if it is in an f-string
    try:
        return fromstring(f"<i>[{inner_html or TEXT_MISSING}]</i>")
    except LxmlError:
        element = Element("i")
        element.text = f"[{TEXT_MISSING}]"
        return element


def _render_link(translation: PageTranslation, inner_html: str | None) -> Element:
    """
    Build the link to the given translation

    :param translation: The translation which is linked to
    :param inner_html: The content of the link, or ``None`` to use the link title of the target
    :return: The link element
    """
    if inner_html is None:
        element = Element("a")
        link_title = translation.link_title
        if isinstance(link_title, str):
            # LXML needs a single root element, so we're doing this in a roundabout way
            root = fromstring(f"<root>{link_title}</root>")
            element.text = root.text
            for child in root:
                element.append(child)
        else:
            # The link title is cached on the translation, so it must not be re-parented
            element.append(deepcopy(link_title))
    else:
        try:
            element = fromstring(f"<a>{inner_html}</a>")
        except LxmlError:
            element = Element("a")
            element.text = inner_html
    # Absolute, because that is what internal links looked like before they were stored as
    # shortcodes: the content delivered to clients has always contained full webapp urls
    element.attrib["href"] = translation.full_url
    hide_anchor_tag_around_single_image(element)
    return element


@shortcode(PAGE_KEYWORD)
def page(
    pargs: list[str],
    kwargs: dict[str, str],  # noqa: ARG001
    context: dict[str, Any] | None,
    content: str = "",  # noqa: ARG001
) -> str:
    """
    Shortcode to insert an internal link to a :class:`~integreat_cms.cms.models.pages.page.Page`.

    Positional arguments:

    * ``page_id``              – The id of the :class:`~integreat_cms.cms.models.pages.page.Page` to which should be linked
    * ``link_text`` (optional) – If not given, the title of the public :class:`~integreat_cms.cms.models.pages.page_translation.PageTranslation` is used

    If the target page has an icon set and the shortcode has no ``link_text``,
    the icon will be included as an ``<ìmg>`` before the page title.

    If the link should wrap html instead of plain text, use
    :func:`~integreat_cms.cms.utils.shortcodes.page.page_link` instead.

    .. list-table:: Examples
        :widths: 30 70
        :header-rows: 0

        * - ``[page 1]``
          - ``<a href="https://integreat.app/augsburg/de/willkommen/">Willkommen</a>``
        * - ``[page 1 "this page"]``
          - ``<a href="https://integreat.app/augsburg/de/willkommen/">this page</a>``
        * - ``[page 999999]``
          - ``<i>[MISSING LINK]</i>``
    """
    page_id = pargs[0] if pargs else None
    text = pargs[1] if len(pargs) > 1 else None
    try:
        translation = _get_public_translation(page_id, context)
    except (Page.DoesNotExist, PageTranslation.DoesNotExist):
        element = _missing_link(text or "")
    else:
        element = _render_link(translation, text)
    return tostring(element).decode("utf-8")


@shortcode(PAGE_LINK_KEYWORD, PAGE_LINK_END_KEYWORD)
def page_link(
    pargs: list[str],
    kwargs: dict[str, str],  # noqa: ARG001
    context: dict[str, Any] | None,
    content: str = "",
) -> str:
    """
    Shortcode to wrap its content in an internal link to a :class:`~integreat_cms.cms.models.pages.page.Page`.

    This is the block scoped counterpart of :func:`~integreat_cms.cms.utils.shortcodes.page.page`,
    which is used whenever the content of the link is not plain text, for example a linked image.

    Positional arguments:

    * ``page_id`` – The id of the :class:`~integreat_cms.cms.models.pages.page.Page` to which should be linked

    .. list-table:: Examples
        :widths: 45 55
        :header-rows: 0

        * - ``[page_link 1]<b>hier</b>[/page_link]``
          - ``<a href="https://integreat.app/augsburg/de/willkommen/"><b>hier</b></a>``
        * - ``[page_link 999999]<b>hier</b>[/page_link]``
          - ``<i>[<b>hier</b>]</i>``
    """
    page_id = pargs[0] if pargs else None
    try:
        translation = _get_public_translation(page_id, context)
    except (Page.DoesNotExist, PageTranslation.DoesNotExist):
        element = _missing_link(content)
    else:
        element = _render_link(translation, content)
    return tostring(element).decode("utf-8")
