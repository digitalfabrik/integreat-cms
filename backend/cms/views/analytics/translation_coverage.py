"""Views related to the statistics module"""
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render

from ...models import Language, Page, PageTranslation
from ...decorators import region_permission_required


@method_decorator(login_required, name='dispatch')
@method_decorator(region_permission_required, name='dispatch')
class TranslationCoverageView(TemplateView):
    """
    Class to create the statistic page, that can be found via -> "Statistiken"
    """
    template_name = 'analytics/translation_coverage.html'
    base_context = {'current_menu_item': 'translation_coverage'}

    def get(self, request, *args, **kwargs):

        languages = Language.objects.all()

        languages = list(map(lambda x: [x.code, x.name, x.id], languages))

        all_pages = Page.objects.count()

        # pylint: disable=C0200
        for i in range(len(languages)):
            translated_count = PageTranslation.objects.filter(language_id=languages[i][2]).count()
            languages[i].append(translated_count)
            languages[i].append(all_pages - languages[i][3])

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                'coverages': languages
            }
        )
