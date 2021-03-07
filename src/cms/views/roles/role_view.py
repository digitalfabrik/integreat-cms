from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import Group as Role
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...decorators import staff_required
from ...forms import RoleForm


@method_decorator(login_required, name="dispatch")
@method_decorator(staff_required, name="dispatch")
class RoleView(PermissionRequiredMixin, TemplateView):
    """
    View for the role form
    """

    #: Required permission of this view (see :class:`~django.contrib.auth.mixins.PermissionRequiredMixin`)
    permission_required = "auth.change_group"
    #: Whether or not an exception should be raised if the user is not logged in (see :class:`~django.contrib.auth.mixins.LoginRequiredMixin`)
    raise_exception = True

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "roles/role.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    base_context = {"current_menu_item": "roles"}

    def get(self, request, *args, **kwargs):
        """
        Render :class:`~cms.forms.roles.role_form.RoleForm`

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        role_id = kwargs.get("role_id")
        if role_id:
            role = Role.objects.get(id=role_id)
            form = RoleForm(instance=role)
        else:
            form = RoleForm()
        return render(request, self.template_name, {"form": form, **self.base_context})

    def post(self, request, role_id=None):
        """
        Submit :class:`~cms.forms.roles.role_form.RoleForm` and save :class:`~django.contrib.auth.models.Group` object

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param role_id: The id of the role which should be edited
        :type role_id: int

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        # TODO: error handling
        if role_id:
            role = Role.objects.get(id=role_id)
            form = RoleForm(request.POST, instance=role)
            success_message = _("Role was successfully saved")
        else:
            form = RoleForm(request.POST)
            success_message = _("Role was successfully created")
        if form.is_valid():
            form.save()
            messages.success(request, success_message)
        else:
            # TODO: improve messages
            messages.error(request, _("Errors have occurred"))

        return render(request, self.template_name, {"form": form, **self.base_context})
