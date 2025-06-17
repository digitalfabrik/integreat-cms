from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..cms.models import Language, Page

logger = logging.getLogger(__name__)


def get_translation_slug(
    pages: list[Page], languages: list[Language]
) -> dict[int, dict[str, str]]:
    """
    Produce mapping of page ids and language slugs to the absolute url of the corresponding translation.
    In detail, we need to construct a slug in the foreign language, for example /en/lebensmittel-und-einkaufen needs to become /en/groceries-and-shopping.

    :param pages: The list of pages for which we want the absolute url of
    :param languages: The list of languages for which we want the absolute url of
    :return: A dictionary of page ids, language slugs and the absolute url of the corresponding translation.
    """
    translation_slugs: dict = {}
    for page in pages:
        for language in languages:
            if page_translation := page.get_translation(language.slug):
                if page.id not in translation_slugs:
                    translation_slugs[page.id] = {}
                translation_slugs[page.id][language.slug] = (
                    page_translation.get_absolute_url().rstrip("/")
                )
    return translation_slugs
