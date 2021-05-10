import logging

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render

from ...constants import translation_status
from ...models import PageTranslation, Region
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
        """
        Render the translation coverage

        :param request: Object representing the user call
        :type request: ~django.http.HttpRequest

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        region = Region.get_current_region(request)

        total_number_pages = region.pages.count()

        translation_coverage_data = []
        outdated_word_count = {}

        for language in region.languages:
            # Get all page translation of this region and language
            page_translations = PageTranslation.get_translations(region, language)

            # Get the QuerySet of translations which are currently not in translation (so either up-to-date or outdated)
            currently_not_in_translation = page_translations.filter(
                currently_in_translation=False
            )
            # Get a list of translations which are outdated
            outdated_page_translations = [
                translation
                for translation in currently_not_in_translation
                if translation.is_outdated
            ]
            # Count the words in the outdated translations
            outdated_word_count[language] = sum(
                len(translation.text.split())
                for translation in outdated_page_translations
            )
            # Count the outdated translations
            outdated_count = len(outdated_page_translations)
            # Append the translation coverage data for this language
            translation_coverage_data.append(
                {
                    # The number of pages which do not have a translation in this language
                    translation_status.MISSING: (
                        total_number_pages - page_translations.count()
                    ),
                    # The number of translations which are outdated
                    translation_status.OUTDATED: outdated_count,
                    # The number of translations which are currently being translated
                    translation_status.IN_TRANSLATION: (
                        page_translations.count() - currently_not_in_translation.count()
                    ),
                    # The number of up-to-date translations (neither missing, nor currently in translation, nor outdated)
                    translation_status.UP_TO_DATE: (
                        currently_not_in_translation.count() - outdated_count
                    ),
                }
            )
            logger.debug(
                "Coverage data for %r: %r", language, translation_coverage_data[-1]
            )

        logger.debug("Outdated word count: %r", outdated_word_count)

        # Assemble the ChartData in the format expected by ChartJS (one dataset for each translation status)
        chart_data = {
            "labels": [language.translated_name for language in region.languages],
            "datasets": [
                {
                    "label": label,
                    "backgroundColor": translation_status.COLORS[status],
                    "data": [data[status] for data in translation_coverage_data],
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
                "outdated_word_count": outdated_word_count,
                "total_outdated_words": sum(outdated_word_count.values()),
            },
        )
