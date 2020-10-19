"""
View to build up the admin dashboard.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...decorators import staff_required


@method_decorator(login_required, name="dispatch")
@method_decorator(staff_required, name="dispatch")
class AdminDashboardView(TemplateView):
    """
    View class representing the Dashboard

    :param: View inherits from the django TemplateView class
    :type: ~django.views.generic.TemplateView
    """

    template_name = "dashboard/admin_dashboard.html"
    base_context = {"current_menu_item": "admin_dashboard"}

    def get(self, request, *args, **kwargs):
        """
        Render Admin Dashboard

        :param request: Object representing the user call
        :type request: ~django.http.HttpRequest

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        val = "To be defined"
        return render(request, self.template_name, {"key": val, **self.base_context})
