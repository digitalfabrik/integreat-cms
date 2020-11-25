from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render

from ...decorators import staff_required
from ...models import OfferTemplate


@method_decorator(login_required, name="dispatch")
@method_decorator(staff_required, name="dispatch")
class OfferTemplateListView(PermissionRequiredMixin, TemplateView):
    """
    View for listing offer templates
    """

    #: Required permission of this view (see :class:`~django.contrib.auth.mixins.PermissionRequiredMixin`)
    permission_required = "cms.manage_offer_templates"
    #: Whether or not an exception should be raised if the user is not logged in (see :class:`~django.contrib.auth.mixins.LoginRequiredMixin`)
    raise_exception = True
    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "offer_templates/offer_template_list.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    base_context = {"current_menu_item": "offer_templates"}

    def get(self, request, *args, **kwargs):
        """
        Render offer template list

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        offer_templates = OfferTemplate.objects.all()

        return render(
            request,
            self.template_name,
            {**self.base_context, "offer_templates": offer_templates},
        )
