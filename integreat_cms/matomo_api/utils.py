from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..cms.models.pages.page_translation import PageTranslation

logger = logging.getLogger(__name__)


def get_translation_slug(
    region_slug: str,
    prefetched_translations: list[PageTranslation],
) -> dict[int, dict[str, str]]:
    """
    Produce mapping of page ids and language slugs to the absolute url of the corresponding translation.
    In detail, we need to construct a slug in the foreign language, for example /en/lebensmittel-und-einkaufen needs to become /en/groceries-and-shopping.

    :param region_slug: Slug of the region we want the absolute url of
    :param prefetched_translations: List of prefetched Pagetranslations that we want the absolute urls of
    :return: A dictionary of page ids, language slugs and the absolute url of the corresponding translation.
    """
    translation_slugs: dict = {}
    for page_translation in prefetched_translations:
        page_id = page_translation.page.id
        language_slug = page_translation.language.slug
        absolute_url = page_translation.slug
        absolute_url = build_infix_recursively(
            absolute_url=absolute_url,
            language_slug=language_slug,
            current_page_translation=page_translation,
            prefetched_translations=prefetched_translations,
        )
        absolute_url = "/" + region_slug + "/" + language_slug + "/" + absolute_url
        if page_id not in translation_slugs:
            translation_slugs[page_id] = {}
        translation_slugs[page_id][language_slug] = absolute_url

    return translation_slugs


def build_infix_recursively(
    absolute_url: str,
    language_slug: str,
    current_page_translation: PageTranslation,
    prefetched_translations: list[PageTranslation],
) -> str:
    """
    Build infix of the absolute url of a PageTranslation object from the prefetched PageTranslations recursively. This is a workaround to avoid calling the cache, which is needed when page accesses are fetched with celery.

    :param absolut_url: absolute url build at hte point of calling
    :param language_slug: Language slug of the current page translation
    :param current_page_translation: Page translation for that we want the parent slug of
    :param prefetched_translations: List with prefetched page translations we select from
    :return: A string containing the url build until the point of calling. At the end of the recursion it returns the absolute url of the page translation from the first call
    """
    if current_page_translation.page.parent:
        parent = current_page_translation.page.parent
        for page_translation in prefetched_translations:
            if (
                page_translation.page == parent
                and page_translation.language.slug == language_slug
            ):
                parent_translation_slug = page_translation.slug
                absolute_url = parent_translation_slug + "/" + absolute_url
                current_page_translation = page_translation
                return build_infix_recursively(
                    absolute_url=absolute_url,
                    language_slug=language_slug,
                    current_page_translation=current_page_translation,
                    prefetched_translations=prefetched_translations,
                )
    return absolute_url
