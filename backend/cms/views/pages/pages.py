from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView
from django.shortcuts import render, redirect

from ...models import Page, Site, Language
from ...decorators import region_permission_required


@method_decorator(login_required, name='dispatch')
@method_decorator(region_permission_required, name='dispatch')
class PageTreeView(TemplateView):
    template_name = 'pages/tree.html'
    base_context = {'current_menu_item': 'pages'}

    def get(self, request, *args, **kwargs):
        # current site
        site_slug = kwargs.get('site_slug')
        site = Site.objects.get(slug=site_slug)

        # current language
        language_code = kwargs.get('language_code', None)
        if language_code:
            language = Language.objects.get(code=language_code)
        elif site.default_language:
            return redirect('pages', **{
                'site_slug': site_slug,
                'language_code': site.default_language.code,
            })
        else:
            messages.error(
                request,
                _('Please create at least one language node before creating pages.')
            )
            return redirect('language_tree', **{
                'site_slug': site_slug,
            })

        # all pages of the current site in the current language
        pages = Page.get_tree(site_slug)
        
        # all other languages of current site
        languages = site.languages

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                'pages': pages,
                'archived_count': Page.archived_count(site_slug),
                'language': language,
                'languages': languages,
            }
        )
