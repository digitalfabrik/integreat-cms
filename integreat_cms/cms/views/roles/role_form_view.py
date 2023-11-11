from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from ...decorators import permission_required
from ...forms import GroupForm, RoleForm
from ...models import Role

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


@method_decorator(permission_required("auth.view_group"), name="dispatch")
@method_decorator(permission_required("auth.change_group"), name="post")
class RoleFormView(TemplateView):
    """
    View for the role form
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "roles/role_form.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    extra_context = {"current_menu_item": "roles"}

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Render :class:`~integreat_cms.cms.forms.roles.role_form.RoleForm`

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
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
            {
                **self.get_context_data(**kwargs),
                "role_form": role_form,
                "group_form": group_form,
            },
        )

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Submit :class:`~integreat_cms.cms.forms.roles.role_form.RoleForm` and save :class:`~django.contrib.auth.models.Group` object

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
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
            else:
                # Add the success message
                messages.success(
                    request,
                    _('Role "{}" was successfully saved').format(role_form.instance),
                )
            return redirect(
                "edit_role",
                role_id=role_form.instance.id,
            )

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "role_form": role_form,
                "group_form": group_form,
            },
        )
