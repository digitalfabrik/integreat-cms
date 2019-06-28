"""
View to build up the admin dashboard.
"""
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render

from ...decorators import staff_required


@method_decorator(login_required, name='dispatch')
@method_decorator(staff_required, name='dispatch')
class AdminDashboardView(TemplateView):
    """View class representing the Dashboard

    Args:
        TemplateView : View inherits from the django TemplateView class

    Returns:
        View : Rendered HTML-Page that will be seen in the CMS-Dashboard
    """

    template_name = 'general/admin_dashboard.html'
    base_context = {'current_menu_item': 'admin_dashboard'}

    def get(self, request, *args, **kwargs):
        val = 'To be defined'
        return render(request, self.template_name,
                      {'key': val, **self.base_context})
