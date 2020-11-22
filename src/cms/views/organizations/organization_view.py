from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...decorators import staff_required
from ...forms.organizations import OrganizationForm
from ...models import Organization


@method_decorator(login_required, name="dispatch")
@method_decorator(staff_required, name="dispatch")
class OrganizationView(PermissionRequiredMixin, TemplateView):
    """
    View for the organization form
    """

    #: Required permission of this view (see :class:`~django.contrib.auth.mixins.PermissionRequiredMixin`)
    permission_required = "cms.manage_organizations"
    #: Whether or not an exception should be raised if the user is not logged in (see :class:`~django.contrib.auth.mixins.LoginRequiredMixin`)
    raise_exception = True
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
        return render(request, self.template_name, {"form": form, **self.base_context})

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
        # TODO: error handling
        if organization_id:
            organization = Organization.objects.get(id=organization_id)
            form = OrganizationForm(request.POST, instance=organization)
            success_message = _("Organization was successfully created")
        else:
            form = OrganizationForm(request.POST)
            success_message = _("Organization was successfully saved")

        if form.is_valid():
            form.save()
            messages.success(request, success_message)
            # TODO: improve messages
        else:
            messages.error(request, _("Errors have occurred."))

        return render(request, self.template_name, {"form": form, **self.base_context})
