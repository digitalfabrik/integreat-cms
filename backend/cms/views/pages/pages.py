from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView
from django.shortcuts import render, redirect

from ...models import Page, Region, Language
from ...decorators import region_permission_required


@method_decorator(login_required, name='dispatch')
@method_decorator(region_permission_required, name='dispatch')
class PageTreeView(PermissionRequiredMixin, TemplateView):
    permission_required = 'cms.view_pages'
    raise_exception = True

    template_name = 'pages/tree.html'
    base_context = {'current_menu_item': 'pages'}

    def get(self, request, *args, **kwargs):
        # current region
        region_slug = kwargs.get('region_slug')
        region = Region.objects.get(slug=region_slug)

        # current language
        language_code = kwargs.get('language_code', None)
        if language_code:
            language = Language.objects.get(code=language_code)
        elif region.default_language:
            return redirect('pages', **{
                'region_slug': region_slug,
                'language_code': region.default_language.code,
            })
        else:
            messages.error(
                request,
                _('Please create at least one language node before creating pages.')
            )
            return redirect('language_tree', **{
                'region_slug': region_slug,
            })

        # all pages of the current region in the current language
        pages = Page.get_tree(region_slug)

        # all other languages of current region
        languages = region.languages

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                'pages': pages,
                'archived_count': Page.archived_count(region_slug),
                'language': language,
                'languages': languages,
            }
        )
