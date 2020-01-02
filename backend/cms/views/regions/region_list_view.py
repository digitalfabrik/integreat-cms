from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...decorators import staff_required
from ...models import Region


@method_decorator(login_required, name='dispatch')
@method_decorator(staff_required, name='dispatch')
class RegionListView(PermissionRequiredMixin, TemplateView):
    permission_required = 'cms.manage_regions'
    raise_exception = True

    template_name = 'regions/list.html'
    base_context = {'current_menu_item': 'regions'}

    def get(self, request, *args, **kwargs):
        regions = Region.objects.all()

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                'regions': regions
            }
        )
