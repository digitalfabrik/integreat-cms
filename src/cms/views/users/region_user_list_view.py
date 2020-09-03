from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...decorators import region_permission_required
from ...models import Region


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
class RegionUserListView(PermissionRequiredMixin, TemplateView):
    permission_required = "cms.manage_region_users"
    raise_exception = True

    template_name = "users/region/list.html"
    base_context = {"current_menu_item": "region_users"}

    def get(self, request, *args, **kwargs):

        region = Region.objects.get(slug=kwargs.get("region_slug"))

        region_users = get_user_model().objects.filter(
            profile__regions=region,
            is_superuser=False,
            is_staff=False,
        )

        return render(
            request, self.template_name, {**self.base_context, "users": region_users}
        )
