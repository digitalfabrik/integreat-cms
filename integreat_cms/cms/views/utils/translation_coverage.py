from collections import Counter

from ...constants.translation_status import MISSING, OUTDATED, UP_TO_DATE
from ...models import Language, Region


def get_translation_and_word_count(
    region: Region,
) -> tuple[dict[Language, Counter], dict[Language, Counter]]:
    """
    This function counts the translations and words of a region

    :param region: The region for which we want to count the translation and word count
    :return: The translation and word count in a tuple
    """
    # Initialize dicts which will hold the counter per language
    translation_count: dict[Language, Counter] = {}
    word_count: dict[Language, Counter] = {}

    # Cache the page tree to avoid database overhead
    pages = (
        region.pages.filter(explicitly_archived=False)
        .prefetch_major_translations()
        .cache_tree(archived=False)
    )

    # Ignore all pages which do not have a published translation in the default language
    pages = list(
        filter(
            lambda page: page.get_translation_state(region.default_language.slug)
            == UP_TO_DATE,
            pages,
        )
    )

    # Iterate over all active languages of the current region
    for language in region.active_languages:
        # Only check pages that are not in the default language
        if language == region.default_language:
            continue
        # Initialize counter dicts for both the translation count and the word count
        translation_count[language] = Counter()
        word_count[language] = Counter()

        # Iterate over all non-archived pages
        for page in pages:
            # Retrieve the translation state of the current language
            translation_state = page.get_translation_state(language.slug)
            translation_count[language][translation_state] += 1
            # If the state is either outdated or missing, keep track of the word count
            if translation_state in [OUTDATED, MISSING]:
                # Check word count of translation in source language
                source_language = region.get_source_language(language.slug)
                # If the source translation does not exist, fall back to the default translation
                if source_language is not None and region.default_language is not None:
                    translation = page.get_translation(
                        source_language.slug
                    ) or page.get_translation(region.default_language.slug)
                else:
                    translation = None
                # Provide a rough estimation of the word count
                word_count[language][translation_state] += len(
                    translation.content.split()
                )
    return translation_count, word_count
