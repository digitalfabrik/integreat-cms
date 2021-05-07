from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.shortcuts import render

from ...decorators import region_permission_required


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
class BrokenLinkCheckerView(TemplateView):
    """
    View to show all not-working links in the content.
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "analytics/broken_links.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    base_context = {"current_menu_item": "broken_link"}

    def get(self, request, *args, **kwargs):
        """
        Renders a Template response with an overview of not-working links.

        :param request: Object representing the user call
        :type request: ~django.http.HttpRequest

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        # TODO Implementation
        total_broken_links = []

        return render(
            request,
            self.template_name,
            {**self.base_context, "broken_link": total_broken_links},
        )
