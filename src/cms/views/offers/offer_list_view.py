from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render

from ...decorators import region_permission_required
from ...models import Region, OfferTemplate


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
class OfferListView(PermissionRequiredMixin, TemplateView):
    permission_required = "cms.manage_offers"
    raise_exception = True

    template_name = "offers/offer_list.html"
    base_context = {"current_menu_item": "offers"}

    def get(self, request, *args, **kwargs):
        # current region
        region = Region.get_current_region(request)
        offer_templates = OfferTemplate.objects.all()

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                "offer_templates": offer_templates,
                "region_offer_templates": offer_templates.filter(offers__region=region),
            },
        )
