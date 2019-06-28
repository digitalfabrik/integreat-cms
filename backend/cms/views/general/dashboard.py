"""
View to build up the dashboard.
"""
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render

from ...decorators import region_permission_required


@method_decorator(login_required, name='dispatch')
@method_decorator(region_permission_required, name='dispatch')
class DashboardView(TemplateView):
    """View class representing the Dashboard

    Args:
        TemplateView : View inherits from the django TemplateView class

    Returns:
        View : Rendered HTML-Page that will be seen in the CMS-Dashboard
    """

    template_name = 'general/dashboard.html'
    base_context = {'current_menu_item': 'region_dashboard'}

    def get(self, request, *args, **kwargs):
        val = 'To be defined'
        return render(request, self.template_name,
                      {'key': val, **self.base_context})
