from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render

from ...decorators import staff_required
from ...models import ExtraTemplate


@method_decorator(login_required, name='dispatch')
@method_decorator(staff_required, name='dispatch')
class ExtraTemplateListView(PermissionRequiredMixin, TemplateView):
    permission_required = 'cms.manage_extra_templates'
    raise_exception = True

    template_name = 'extra_templates/extra_template_list.html'
    base_context = {'current_menu_item': 'extra_templates'}

    def get(self, request, *args, **kwargs):
        extra_templates = ExtraTemplate.objects.all()

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                'extra_templates': extra_templates
            }
        )
