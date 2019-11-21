from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView
from django.shortcuts import render, redirect

from ...decorators import region_permission_required
from ...models import Region, Extra, ExtraTemplate


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

@login_required
@region_permission_required
@permission_required('cms.manage_extras', raise_exception=True)
def activate(request, region_slug, extra_template_slug):
    region = Region.objects.get(slug=region_slug)
    template = ExtraTemplate.objects.get(slug=extra_template_slug)
    Extra.objects.create(region=region, template=template)
    messages.success(request, 'Extra "' + template.name + '" ' + _('was successfully activated.'))
    return redirect('extras', **{
        'region_slug': region_slug,
    })

@login_required
@region_permission_required
@permission_required('cms.manage_extras', raise_exception=True)
def deactivate(request, region_slug, extra_template_slug):
    region = Region.objects.get(slug=region_slug)
    template = ExtraTemplate.objects.get(slug=extra_template_slug)
    extra = Extra.objects.filter(region=region, template=template).first()
    extra.delete()
    messages.success(request, 'Extra "' + template.name + '" ' + _('was successfully deactivated.'))
    return redirect('extras', **{
        'region_slug': region_slug,
    })
