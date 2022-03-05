import logging
from collections import Counter

from django.views.generic import TemplateView

from ...constants import translation_status


logger = logging.getLogger(__name__)


class TranslationCoverageView(TemplateView):
    """
    View to calculate and show the translation coverage statistics (up to date translations, missing translation, etc)
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "analytics/translation_coverage.html"

    def get_context_data(self, **kwargs):
        r"""
        Extend context by traanslation coverage data

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The context dictionary
        :rtype: dict
        """

        region = self.request.region

        translation_coverage_data = {}
        outdated_word_count = Counter()

        pages = (
            region.pages.filter(explicitly_archived=False)
            .prefetch_major_public_translations()
            .cache_tree(archived=False)
        )
        for language in region.active_languages:
            language_coverage_data = Counter()
            for page in pages:
                translation_state = page.get_translation_state(language.slug)
                language_coverage_data[translation_state] += 1

                if translation_state == translation_status.OUTDATED:
                    translation = page.get_translation(language.slug)
                    outdated_word_count[language] += len(translation.content.split())
            translation_coverage_data[language] = language_coverage_data

        for (language, data) in translation_coverage_data.items():
            logger.debug(
                "Coverage data for %r: %r",
                language,
                data,
            )
        logger.debug("Outdated word count: %r", outdated_word_count)

        # Assemble the ChartData in the format expected by ChartJS (one dataset for each translation status)
        chart_data = {
            "labels": [
                language.translated_name for language in translation_coverage_data
            ],
            "datasets": [
                {
                    "label": label,
                    "backgroundColor": translation_status.COLORS[status],
                    "data": [
                        data[status] for data in translation_coverage_data.values()
                    ],
                }
                for status, label in translation_status.CHOICES
            ],
        }

        context = super().get_context_data(**kwargs)
        context.update(
            {
                "current_menu_item": "translation_coverage",
                "coverage_data": chart_data,
                "outdated_word_count": dict(outdated_word_count),
                "total_outdated_words": sum(outdated_word_count.values()),
            }
        )
        return context
