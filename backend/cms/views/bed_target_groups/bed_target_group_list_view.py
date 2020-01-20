from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...decorators import staff_required
from ...models import BedTargetGroup


@method_decorator(login_required, name='dispatch')
@method_decorator(staff_required, name='dispatch')
class BedTargetGroupListView(PermissionRequiredMixin, TemplateView):
    permission_required = 'cms.manage_bed_target_groups'
    raise_exception = True

    template_name = 'bed_target_groups/bed_target_group_list.html'
    base_context = {'current_menu_item': 'bed_target_groups'}

    def get(self, request, *args, **kwargs):
        bed_target_groups = BedTargetGroup.objects.all()

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                'bed_target_groups': bed_target_groups
            }
        )
