from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...decorators import staff_required
from ...models import Organization


@method_decorator(login_required, name='dispatch')
@method_decorator(staff_required, name='dispatch')
class OrganizationListView(PermissionRequiredMixin, TemplateView):
    permission_required = 'cms.manage_organizations'
    raise_exception = True

    template_name = 'organizations/organization_list.html'
    base_context = {'current_menu_item': 'organizations'}

    def get(self, request, *args, **kwargs):
        organizations = Organization.objects.all()

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                'organizations': organizations
            }
        )
