from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...decorators import staff_required
from ...forms.bed_target_groups import BedTargetGroupForm
from ...models import BedTargetGroup


@method_decorator(login_required, name='dispatch')
@method_decorator(staff_required, name='dispatch')
class BedTargetGroupView(PermissionRequiredMixin, TemplateView):
    permission_required = 'cms.manage_bed_target_groups'
    raise_exception = True

    template_name = 'bed_target_groups/bed_target_group_form.html'
    base_context = {'current_menu_item': 'bed_target_groups'}

    def get(self, request, *args, **kwargs):

        bed_target_group = BedTargetGroup.objects.filter(id=kwargs.get('bed_target_group_id')).first()
        form = BedTargetGroupForm(instance=bed_target_group)

        return render(request, self.template_name, {
            'form': form,
            **self.base_context
        })

    # pylint: disable=unused-argument
    def post(self, request, *args, **kwargs):

        bed_target_group_instance = BedTargetGroup.objects.filter(id=kwargs.get('bed_target_group_id')).first()
        form = BedTargetGroupForm(request.POST, instance=bed_target_group_instance)

        if form.is_valid():
            bed_target_group = form.save()
            if bed_target_group_instance:
                messages.success(request, _('Bed target group saved successfully'))
            else:
                messages.success(request, _('Bed target group created successfully'))
                return redirect('edit_bed_target_group', **{
                    'bed_target_group_id': bed_target_group.id,
                })
        else:
            # TODO: error handling
            messages.error(request, _('Errors have occurred.'))

        return render(request, self.template_name, {
            'form': form,
            **self.base_context
        })
