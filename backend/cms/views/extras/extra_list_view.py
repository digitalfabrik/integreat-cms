from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render

from ...decorators import region_permission_required
from ...models import Region, ExtraTemplate


@method_decorator(login_required, name='dispatch')
@method_decorator(region_permission_required, name='dispatch')
class ExtraListView(PermissionRequiredMixin, TemplateView):
    permission_required = 'cms.manage_extras'
    raise_exception = True

    template_name = 'extras/list.html'
    base_context = {'current_menu_item': 'extras'}

    def get(self, request, *args, **kwargs):
        # current region
        region_slug = kwargs.get('region_slug')
        region = Region.objects.get(slug=region_slug)

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                'extra_templates': ExtraTemplate.objects.all(),
                'region_extra_templates': [
                    extra.template for extra in region.extras.all()
                ],
            }
        )
