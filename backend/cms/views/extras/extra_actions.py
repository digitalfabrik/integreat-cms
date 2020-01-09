from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.translation import ugettext as _
from django.shortcuts import redirect

from ...decorators import region_permission_required
from ...models import Region, Extra, ExtraTemplate


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
