import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView
from django.shortcuts import render, redirect

from ...decorators import staff_required, permission_required
from ...forms import OfferTemplateForm
from ...models import OfferTemplate

logger = logging.getLogger(__name__)


@method_decorator(login_required, name="dispatch")
@method_decorator(staff_required, name="dispatch")
@method_decorator(permission_required("cms.view_offer_template"), name="dispatch")
@method_decorator(permission_required("cms.edit_offer_template"), name="post")
class OfferTemplateView(TemplateView):
    """
    View for the offer template form
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "offer_templates/offer_template_form.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    base_context = {"current_menu_item": "offer_templates"}

    def get(self, request, *args, **kwargs):
        """
        Render :class:`~integreat_cms.cms.forms.offer_templates.offer_template_form.OfferTemplateForm`

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
        Submit :class:`~integreat_cms.cms.forms.offer_templates.offer_template_form.OfferTemplateForm` and save
        :class:`~integreat_cms.cms.models.offers.offer_template.OfferTemplate` object

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param offer_template_id: The id of the edited offer template
        :type offer_template_id: int

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        offer_template_instance = OfferTemplate.objects.filter(
            id=offer_template_id
        ).first()

        form = OfferTemplateForm(data=request.POST, instance=offer_template_instance)

        if not form.is_valid():
            # Add error messages
            form.add_error_messages(request)
        elif not form.has_changed():
            # Add "no changes" messages
            messages.info(request, _("No changes made"))
        else:
            # Save form
            form.save()
            # Add the success message and redirect to the edit page
            if offer_template_instance:
                messages.success(
                    request,
                    _('Offer template "{}" was successfully created').format(
                        form.instance
                    ),
                )
                return redirect(
                    "edit_offer_template", offer_template_id=form.instance.id
                )
            # Add the success message
            messages.success(
                request,
                _('Offer template "{}" was successfully saved').format(form.instance),
            )

        return render(request, self.template_name, {"form": form, **self.base_context})
