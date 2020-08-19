from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...decorators import staff_required


@method_decorator(login_required, name="dispatch")
@method_decorator(staff_required, name="dispatch")
class UserListView(PermissionRequiredMixin, TemplateView):
    permission_required = "cms.manage_admin_users"
    raise_exception = True

    template_name = "users/admin/list.html"
    base_context = {"current_menu_item": "users"}

    def get(self, request, *args, **kwargs):
        users = get_user_model().objects.all()

        return render(
            request, self.template_name, {**self.base_context, "users": users}
        )
