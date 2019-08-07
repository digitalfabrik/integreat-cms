from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView
from django.shortcuts import render, redirect

from ...models import Region, Language
from ...decorators import region_permission_required


@method_decorator(login_required, name='dispatch')
@method_decorator(region_permission_required, name='dispatch')
class POIListView(PermissionRequiredMixin, TemplateView):
    permission_required = 'cms.manage_pois'
    raise_exception = True

    template_name = 'pois/list.html'
    base_context = {'current_menu_item': 'pois'}

    def get(self, request, *args, **kwargs):
        # current region
        region_slug = kwargs.get('region_slug')
        region = Region.objects.get(slug=region_slug)

        # current language
        language_code = kwargs.get('language_code', None)
        if language_code:
            language = Language.objects.get(code=language_code)
        elif region.default_language:
            return redirect('pois', **{
                'region_slug': region_slug,
                'language_code': region.default_language.code,
            })
        else:
            messages.error(
                request,
                _('Please create at least one language node before creating pois.')
            )
            return redirect('language_tree', **{
                'region_slug': region_slug,
            })

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                'pois': region.pois.all(),
                'language': language,
                'languages': region.languages,
            }
        )
