from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView
from django.shortcuts import render, redirect

from ...decorators import staff_required
from ...forms import OfferTemplateForm
from ...models import OfferTemplate


@method_decorator(login_required, name="dispatch")
@method_decorator(staff_required, name="dispatch")
class OfferTemplateView(PermissionRequiredMixin, TemplateView):
    """
    View for the offer template form
    """

    #: Required permission of this view (see :class:`~django.contrib.auth.mixins.PermissionRequiredMixin`)
    permission_required = "cms.manage_offer_templates"
    #: Whether or not an exception should be raised if the user is not logged in (see :class:`~django.contrib.auth.mixins.LoginRequiredMixin`)
    raise_exception = True
    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "offer_templates/offer_template_form.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    base_context = {"current_menu_item": "offer_templates"}

    def get(self, request, *args, **kwargs):
        """
        Render :class:`~cms.forms.offer_templates.offer_template_form.OfferTemplateForm`

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        offer_template_id = kwargs.get("offer_template_id")
        if offer_template_id:
            offer_template = OfferTemplate.objects.get(id=offer_template_id)
            form = OfferTemplateForm(instance=offer_template)
        else:
            form = OfferTemplateForm()
        return render(request, self.template_name, {"form": form, **self.base_context})

    def post(self, request, offer_template_id=None):
        """
        Submit :class:`~cms.forms.offer_templates.offer_template_form.OfferTemplateForm` and save
        :class:`~cms.models.offers.offer_template.OfferTemplate` object

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param offer_template_id: The id of the edited offer template
        :type offer_template_id: int

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        if offer_template_id:
            offer_template = OfferTemplate.objects.get(id=offer_template_id)
            form = OfferTemplateForm(request.POST, instance=offer_template)
            success_message = _("Offer template was successfully saved")
        else:
            form = OfferTemplateForm(request.POST)
            success_message = _("Offer template was successfully created")

        if form.is_valid():
            messages.success(request, success_message)
            offer_template = form.save()
            return redirect(
                "edit_offer_template", **{"offer_template_id": offer_template.id}
            )

        messages.error(request, _("Errors have occurred."))
        # TODO: improve messages
        return render(request, self.template_name, {"form": form, **self.base_context})
