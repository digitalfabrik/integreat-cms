import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...decorators import staff_required, permission_required
from ...forms import OrganizationForm
from ...models import Organization
from ..media.media_context_mixin import MediaContextMixin


logger = logging.getLogger(__name__)


@method_decorator(login_required, name="dispatch")
@method_decorator(staff_required, name="dispatch")
@method_decorator(permission_required("cms.view_organization"), name="dispatch")
@method_decorator(permission_required("cms.change_organization"), name="post")
class OrganizationView(TemplateView, MediaContextMixin):
    """
    View for the organization form
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "organizations/organization_form.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    base_context = {"current_menu_item": "organizations"}

    def get(self, request, *args, **kwargs):
        """
        Render :class:`~cms.forms.organizations.organization_form.OrganizationForm`

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        organization_id = kwargs.get("organization_id")
        if organization_id:
            organization = Organization.objects.get(id=organization_id)
            form = OrganizationForm(instance=organization)
        else:
            form = OrganizationForm()

        context = self.get_context_data(**kwargs)
        return render(
            request, self.template_name, {**self.base_context, **context, "form": form}
        )

    def post(self, request, organization_id=None):
        """
        Submit :class:`~cms.forms.organizations.organization_form.OrganizationForm` and save
        :class:`~cms.models.users.organization.Organization` object

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param organization_id: The id of the organization
        :type organization_id: int

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        organization_instance = Organization.objects.filter(id=organization_id).first()
        form = OrganizationForm(
            data=request.POST, files=request.FILES, instance=organization_instance
        )

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
            if not organization_instance:
                messages.success(
                    request,
                    _('Organization "{}" was successfully created').format(
                        form.instance
                    ),
                )
                return redirect(
                    "edit_organization",
                    organization_id=form.instance.id,
                )
            # Add the success message
            messages.success(
                request,
                _('Organization "{}" was successfully saved').format(form.instance),
            )

        return render(request, self.template_name, {"form": form, **self.base_context})
