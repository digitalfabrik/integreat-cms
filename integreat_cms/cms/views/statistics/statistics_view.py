"""Views related to the statistics module"""
import logging

from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView


from ...forms import StatisticsFilterForm

logger = logging.getLogger(__name__)


class AnalyticsView(TemplateView):
    """
    View for the statistics overview.
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "statistics/statistics_overview.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    extra_context = {"current_menu_item": "statistics"}

    # pylint: disable=unused-variable
    def get(self, request, *args, **kwargs):
        r"""
        Render statistics of access numbers tracked by Matomo

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        region = request.region

        if not region.statistics_enabled:
            messages.error(request, _("Statistics are not enabled for this region."))
            return redirect(
                "dashboard",
                **{
                    "region_slug": region.slug,
                }
            )

        form = StatisticsFilterForm()

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "form": form,
            },
        )
