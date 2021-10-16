import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...decorators import staff_required, permission_required
from ...forms import RoleForm, GroupForm
from ...models import Role

logger = logging.getLogger(__name__)


@method_decorator(login_required, name="dispatch")
@method_decorator(staff_required, name="dispatch")
@method_decorator(permission_required("auth.view_group"), name="dispatch")
@method_decorator(permission_required("auth.change_group"), name="post")
class RoleView(TemplateView):
    """
    View for the role form
    """

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
        role_instance = (
            Role.objects.filter(id=kwargs.get("role_id"))
            .select_related("group")
            .first()
        )
        role_form = RoleForm(instance=role_instance)
        group_form = GroupForm(instance=getattr(role_instance, "group", None))
        return render(
            request,
            self.template_name,
            {"role_form": role_form, "group_form": group_form, **self.base_context},
        )

    # pylint: disable=unused-argument
    def post(self, request, *args, **kwargs):
        """
        Submit :class:`~cms.forms.roles.role_form.RoleForm` and save :class:`~django.contrib.auth.models.Group` object

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        role_instance = (
            Role.objects.filter(id=kwargs.get("role_id"))
            .select_related("group")
            .first()
        )
        role_form = RoleForm(data=request.POST, instance=role_instance)
        group_form = GroupForm(
            data=request.POST, instance=getattr(role_instance, "group", None)
        )

        if not role_form.is_valid() or not group_form.is_valid():
            # Add error messages
            role_form.add_error_messages(request)
        elif not role_form.has_changed() and not group_form.has_changed():
            # Add "no changes" messages
            messages.info(request, _("No changes made"))
        else:
            # Save forms
            role_form.instance.group = group_form.save()
            role_form.save()
            # Add the success message and redirect to the edit page
            if not role_instance:
                messages.success(
                    request,
                    _('Role "{}" was successfully created').format(role_form.instance),
                )
                return redirect(
                    "edit_role",
                    role_id=role_form.instance.id,
                )
            # Add the success message
            messages.success(
                request,
                _('Role "{}" was successfully saved').format(role_form.instance),
            )

        return render(
            request,
            self.template_name,
            {"role_form": role_form, "group_form": group_form, **self.base_context},
        )
