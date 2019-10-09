from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView
from django.shortcuts import render, redirect

from .extra_template_form import ExtraTemplateForm
from ...models.extra_template import ExtraTemplate
from ...decorators import staff_required


@method_decorator(login_required, name='dispatch')
@method_decorator(staff_required, name='dispatch')
class ExtraTemplateListView(PermissionRequiredMixin, TemplateView):
    permission_required = 'cms.manage_extra_templates'
    raise_exception = True

    template_name = 'extra_templates/list.html'
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


@method_decorator(login_required, name='dispatch')
@method_decorator(staff_required, name='dispatch')
class ExtraTemplateView(PermissionRequiredMixin, TemplateView):
    permission_required = 'cms.manage_extra_templates'
    raise_exception = True

    template_name = 'extra_templates/extra_template.html'
    base_context = {'current_menu_item': 'extra_templates'}

    def get(self, request, *args, **kwargs):
        extra_template_id = self.kwargs.get('extra_template_id', None)
        if extra_template_id:
            extra_template = ExtraTemplate.objects.get(id=extra_template_id)
            form = ExtraTemplateForm(instance=extra_template)
        else:
            form = ExtraTemplateForm()
        return render(request, self.template_name, {
            'form': form,
            **self.base_context
        })

    def post(self, request, extra_template_id=None):

        if extra_template_id:
            extra_template = ExtraTemplate.objects.get(id=extra_template_id)
            form = ExtraTemplateForm(request.POST, instance=extra_template)
            success_message = _('Extra template saved successfully')
        else:
            form = ExtraTemplateForm(request.POST)
            success_message = _('Extra template created successfully')

        if form.is_valid():
            messages.success(request, success_message)
            extra_template = form.save()
            return redirect('edit_extra_template', **{
                'extra_template_id': extra_template.id
            })

        messages.error(request, _('Errors have occurred.'))
        # TODO: improve messages
        return render(request, self.template_name, {
            'form': form,
            **self.base_context
        })
