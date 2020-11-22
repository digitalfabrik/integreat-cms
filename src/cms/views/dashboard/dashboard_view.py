from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...decorators import region_permission_required


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
class DashboardView(TemplateView):
    """
    View for the region dashboard
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "dashboard/dashboard.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    base_context = {"current_menu_item": "region_dashboard"}

    def get(self, request, *args, **kwargs):
        """
        Render the region dashboard

        :param request: Object representing the user call
        :type request: ~django.http.HttpRequest

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        val = "To be defined"
        return render(request, self.template_name, {"key": val, **self.base_context})
