from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import Group as Role
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...decorators import staff_required


@method_decorator(login_required, name="dispatch")
@method_decorator(staff_required, name="dispatch")
class RoleListView(PermissionRequiredMixin, TemplateView):
    permission_required = "auth.change_group"
    raise_exception = True

    template_name = "roles/list.html"
    base_context = {"current_menu_item": "roles"}

    def get(self, request, *args, **kwargs):
        roles = Role.objects.all()

        return render(
            request, self.template_name, {**self.base_context, "roles": roles}
        )
