from __future__ import annotations

from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from django.db.models.query import QuerySet
    from ..cms.models import Language, Page


"""def create_translation_slugs(
    pages: QuerySet[Page], languages: list[Language]
) -> dict[Page, dict[str, str]]:
    This function creates the translation slug for the matomo call. It returns then language_slug and the slug in the target translation.
    translation_slugs: Dict[Page, Dict[str, str]] = {}
    for page in pages:
        translation_slugs[page] = {}
        for language in languages:
            if page_translation := page.get_translation(language.slug):
                # print(page_translation.ancestor_path)Sollen wir uns Sol
                translation_slugs[page][language.slug] = page_translation.slug
    return translation_slugs
    """

def get_translation_slug(pages: list[Page], languages: list[Language]) -> dict[int, dict[str, str]]:
    translation_slugs = {}
    for page in pages:
        for language in languages:
            if page_translation := page.get_translation(language.slug):
                if page.id not in translation_slugs:
                    translation_slugs[page.id] = {}
                translation_slugs[page.id][language.slug] = f"{language.slug}/{page_translation.slug}" # nach richtigen Slug noch mal recherchieren
    return translation_slugs

