import logging
from collections import Counter

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render

from ...constants import translation_status
from ...decorators import region_permission_required


logger = logging.getLogger(__name__)


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
class TranslationCoverageView(TemplateView):
    """
    View to calculate and show the translation coverage statistics (up to date translations, missing translation, etc)
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "analytics/translation_coverage.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    base_context = {"current_menu_item": "translation_coverage"}

    def get(self, request, *args, **kwargs):
        r"""
        Render the translation coverage

        :param request: Object representing the user call
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        region = request.region

        translation_coverage_data = {}
        outdated_word_count = Counter()

        pages = region.pages.filter(explicitly_archived=False).cache_tree(
            archived=False
        )[0]
        for language in region.active_languages:
            language_coverage_data = Counter()
            for page in pages:
                translation_state = page.get_translation_state(language)
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

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                "coverage_data": chart_data,
                "outdated_word_count": dict(outdated_word_count),
                "total_outdated_words": sum(outdated_word_count.values()),
            },
        )
