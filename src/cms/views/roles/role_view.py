from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import Group as Role
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...decorators import staff_required
from ...forms.roles import RoleForm


@method_decorator(login_required, name="dispatch")
@method_decorator(staff_required, name="dispatch")
class RoleView(PermissionRequiredMixin, TemplateView):
    permission_required = "auth.change_group"
    raise_exception = True

    template_name = "roles/role.html"
    base_context = {"current_menu_item": "roles"}

    def get(self, request, *args, **kwargs):
        role_id = kwargs.get("role_id")
        if role_id:
            role = Role.objects.get(id=role_id)
            form = RoleForm(instance=role)
        else:
            form = RoleForm()
        return render(request, self.template_name, {"form": form, **self.base_context})

    def post(self, request, role_id=None):
        # TODO: error handling
        if role_id:
            role = Role.objects.get(id=role_id)
            form = RoleForm(request.POST, instance=role)
            success_message = _("Role saved successfully")
        else:
            form = RoleForm(request.POST)
            success_message = _("Role created successfully")
        if form.is_valid():
            form.save()
            messages.success(request, success_message)
        else:
            # TODO: improve messages
            messages.error(request, _("Errors have occurred."))

        return render(request, self.template_name, {"form": form, **self.base_context})
