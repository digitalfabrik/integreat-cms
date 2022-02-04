import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render

from ...decorators import staff_required, permission_required
from ...models import OfferTemplate

logger = logging.getLogger(__name__)


@method_decorator(login_required, name="dispatch")
@method_decorator(staff_required, name="dispatch")
@method_decorator(permission_required("cms.view_offer_template"), name="dispatch")
class OfferTemplateListView(TemplateView):
    """
    View for listing offer templates
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "offertemplates/offertemplate_list.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    extra_context = {"current_menu_item": "offertemplates"}

    def get(self, request, *args, **kwargs):
        r"""
        Render offer template list

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        offer_templates = OfferTemplate.objects.all().prefetch_related("regions")
        chunk_size = int(request.GET.get("size", settings.PER_PAGE))
        # for consistent pagination querysets should be ordered
        paginator = Paginator(offer_templates.order_by("slug"), chunk_size)
        chunk = request.GET.get("page")
        offer_templates_chunk = paginator.get_page(chunk)
        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "offer_templates": offer_templates_chunk,
            },
        )
