from __future__ import annotations

import logging
from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..cms.models.pages.page_translation import PageTranslation

logger = logging.getLogger(__name__)


def get_translation_slug(
    prefetched_translations: list[PageTranslation],
) -> defaultdict[int, defaultdict[str, dict[int, str]]]:
    """
    Produce mapping of page ids and language slugs to all slug versions of the corresponding page translation objects.

    :param prefetched_translations: List of prefetched Pagetranslations that we want the mapping for
    :return: A dictionary of page ids, language slugs and all slug versions of the corresponding translation.
    """
    translation_slugs: defaultdict[int, defaultdict[str, dict[int, str]]] = defaultdict(
        lambda: defaultdict(dict)
    )
    for page_translation in prefetched_translations:
        page_id = page_translation.page.id
        language_slug = page_translation.language.slug
        translation_version = page_translation.version
        translation_slug = page_translation.slug
        translation_slugs[page_id][language_slug][translation_version] = (
            translation_slug
        )

    return translation_slugs
