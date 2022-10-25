import logging
from collections import Counter

from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from ...decorators import permission_required

from ...constants.translation_status import (
    CHOICES,
    COLORS,
    MISSING,
    OUTDATED,
    UP_TO_DATE,
)


logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_translation_report"), name="dispatch")
class TranslationCoverageView(TemplateView):
    """
    View to calculate and show the translation coverage statistics (up to date translations, missing translation, etc)
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "analytics/translation_coverage.html"

    # pylint: disable=too-many-locals
    def get_context_data(self, **kwargs):
        r"""
        Extend context by translation coverage data

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The context dictionary
        :rtype: dict
        """
        # The current region
        region = self.request.region
        # Initialize dicts which will hold the counter per language
        translation_count = {}
        word_count = {}
        # Cache the page tree to avoid database overhead
        pages = (
            region.pages.filter(explicitly_archived=False)
            .prefetch_major_public_translations()
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
                    translation = page.get_translation(
                        source_language.slug
                    ) or page.get_translation(region.default_language.slug)
                    # Provide a rough estimation of the word count
                    word_count[language][translation_state] += len(
                        translation.content.split()
                    )
        logger.debug("Translation status count: %r", translation_count)
        logger.debug("Word count: %r", word_count)
        # Assemble the ChartData in the format expected by ChartJS (one dataset for each translation status)
        chart_data = {
            "labels": [language.translated_name for language in translation_count],
            "datasets": [
                {
                    "label": label,
                    "backgroundColor": COLORS[status],
                    "data": [data[status] for data in translation_count.values()],
                }
                for status, label in CHOICES
            ],
        }
        # Update and return the template context
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "current_menu_item": "translation_coverage",
                "chart_data": chart_data,
                "word_count": word_count,
                "total_outdated_words": sum(c[OUTDATED] for c in word_count.values()),
                "total_missing_words": sum(c[MISSING] for c in word_count.values()),
            }
        )
        return context
