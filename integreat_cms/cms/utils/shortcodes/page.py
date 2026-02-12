from typing import Any

from django.utils.translation import gettext_lazy as _
from lxml.html import Element, fromstring, tostring

from ...models import Page, PageTranslation
from .utils import shortcode


@shortcode
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

    .. list-table:: Examples
        :widths: 30 70
        :header-rows: 0

        * - ``[page 1]``
          - ``<a href="/augsburg/de/willkommen/">Willkommen</a>``
        * - ``[page 1 "this page"]``
          - ``<a href="/augsburg/de/willkommen/">this page</a>``
        * - ``[page 999999]``
          - ``<i>[MISSING LINK]</i>``
    """
    page_id = pargs[0] if pargs else None
    text = pargs[1] if len(pargs) > 1 else None
    try:
        page = Page.objects.get(id=page_id)
        translation = page.get_public_translation(
            (context or {}).get("language_slug", page.region.default_language.slug)
        )
        if translation is None:
            raise PageTranslation.DoesNotExist  # noqa: TRY301  # But… I want the two lines handling this to not be duplicated
    except (Page.DoesNotExist, PageTranslation.DoesNotExist):
        element = Element("i")
        TEXT_MISSING = _(
            "MISSING LINK"
        )  # Separate variable because gettext apparently does not find _() if it is in an f-string
        element.text = f"[{text or TEXT_MISSING}]"
    else:
        element = Element("a")
        if text is None:
            # LXML needs a single root element, so we're doing this in a roundabout way
            root = fromstring(f"<root>{translation.link_title}</root>")
            element.text = root.text
            for child in root:
                element.append(child)
        else:
            element.text = text or ""
        element.attrib["href"] = translation.get_absolute_url()
    return tostring(element).decode("utf-8")
