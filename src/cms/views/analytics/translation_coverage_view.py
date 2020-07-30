"""Views related to the statistics module"""
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render

from ...models import PageTranslation, Region
from ...decorators import region_permission_required


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
class TranslationCoverageView(TemplateView):
    """
    Class to create the translation coverage statistic
    """

    template_name = "analytics/translation_coverage.html"
    base_context = {"current_menu_item": "translation_coverage"}

    def get(self, request, *args, **kwargs):

        region = Region.get_current_region(request)
        num_pages = region.pages.count()
        languages = []

        for language in region.languages:
            page_translations = PageTranslation.get_translations(region, language)
            languages.append(
                {
                    "translated_name": language.translated_name,
                    "num_page_translations_up_to_date": len(
                        [t for t in page_translations if t.is_up_to_date]
                    ),
                    "num_page_translations_currently_in_translation": len(
                        [t for t in page_translations if t.currently_in_translation]
                    ),
                    "num_page_translations_outdated": len(
                        [t for t in page_translations if t.is_outdated]
                    ),
                    "num_page_translations_missing": num_pages
                    - page_translations.count(),
                }
            )

        return render(
            request, self.template_name, {**self.base_context, "languages": languages}
        )
