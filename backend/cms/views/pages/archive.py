"""
Functionality for providing archive with all pages
"""

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import render, redirect
from django.views.generic import TemplateView

from ...models import Page, Region, Language
from ...decorators import region_permission_required


@method_decorator(login_required, name='dispatch')
@method_decorator(region_permission_required, name='dispatch')
class ArchivedPagesView(TemplateView):
    template_name = 'pages/archive.html'
    base_context = {'current_menu_item': 'pages'}

    def get(self, request, *args, **kwargs):
        # current region
        region_slug = kwargs.get('region_slug')
        region = Region.objects.get(slug=region_slug)

        # all languages of current region
        languages = region.languages

        # current language
        language_code = kwargs.get('language_code', None)
        if language_code:
            language = Language.objects.get(code=language_code)
        elif region.default_language:
            return redirect(
                'pages',
                **{
                    'region_slug': region_slug,
                    'language_code': region.default_language.code,
                }
            )

        # all archived pages of the current region in the current language
        pages = Page.get_archived(region_slug)

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
