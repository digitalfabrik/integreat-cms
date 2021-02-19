from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render

from backend.settings import PER_PAGE
from ...decorators import region_permission_required
from ...models import Region, OfferTemplate


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
class OfferListView(PermissionRequiredMixin, TemplateView):
    """
    View for listing offers
    """

    #: Required permission of this view (see :class:`~django.contrib.auth.mixins.PermissionRequiredMixin`)
    permission_required = "cms.manage_offers"
    #: Whether or not an exception should be raised if the user is not logged in (see :class:`~django.contrib.auth.mixins.LoginRequiredMixin`)
    raise_exception = True
    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "offers/offer_list.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    base_context = {"current_menu_item": "offers"}

    def get(self, request, *args, **kwargs):
        """
        Render offer list

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        # current region
        region = Region.get_current_region(request)
        offer_templates = OfferTemplate.objects.all()
        # for consistent pagination querysets should be ordered
        paginator = Paginator(offer_templates.order_by("slug"), PER_PAGE)
        chunk = request.GET.get("chunk")
        offer_chunk = paginator.get_page(chunk)
        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                "offer_templates": offer_chunk,
                "region_offer_templates": offer_templates.filter(offers__region=region),
            },
        )
