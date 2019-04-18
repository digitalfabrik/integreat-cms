from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render

from ...models import Page, Site, Language


@method_decorator(login_required, name='dispatch')
class PageTreeView(TemplateView):
    template_name = 'pages/tree.html'
    base_context = {'current_menu_item': 'pages'}

    def get(self, request, *args, **kwargs):
        # current site
        site_slug = kwargs.get('site_slug')
        site = Site.objects.get(slug=site_slug)
        # current language
        language_code = kwargs.get('language_code')
        language = Language.objects.get(code=language_code)
        # all pages of the current site in the current language
        pages = Page.get_tree(site_slug, language_code)
        # all other languages of current site
        languages = site.languages

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                'pages': pages,
                'language': language,
                'languages': languages,
            }
        )
