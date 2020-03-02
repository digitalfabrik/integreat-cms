from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.translation import ugettext as _
from django.shortcuts import redirect

from ...decorators import region_permission_required
from ...models import Region, Offer, OfferTemplate


@login_required
@region_permission_required
@permission_required('cms.manage_offers', raise_exception=True)
def activate(request, region_slug, offer_template_slug):
    region = Region.objects.get(slug=region_slug)
    template = OfferTemplate.objects.get(slug=offer_template_slug)
    Offer.objects.create(region=region, template=template)
    messages.success(request, 'Offer "' + template.name + '" ' + _('was successfully activated.'))
    return redirect('offers', **{
        'region_slug': region_slug,
    })

@login_required
@region_permission_required
@permission_required('cms.manage_offers', raise_exception=True)
def deactivate(request, region_slug, offer_template_slug):
    region = Region.objects.get(slug=region_slug)
    template = OfferTemplate.objects.get(slug=offer_template_slug)
    offer = Offer.objects.filter(region=region, template=template).first()
    offer.delete()
    messages.success(request, 'Offer "' + template.name + '" ' + _('was successfully deactivated.'))
    return redirect('offers', **{
        'region_slug': region_slug,
    })
