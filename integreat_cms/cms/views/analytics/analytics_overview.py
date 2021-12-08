from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...decorators import region_permission_required
from ...utils.filter_links import filter_links


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
class AnalyticsView(TemplateView):
    """
    View to show all not-working links in the content.
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "analytics/analytics_overview.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    extra_context = {"current_menu_item": "analytics"}

    def get_context_data(self, **kwargs):
        r"""
        Extend context by amount of links per link filter

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The context dictionary
        :rtype: dict
        """
        context = super().get_context_data(**kwargs)
        _, count_dict = filter_links(kwargs.get("region_slug"))
        context.update(count_dict)
        return context
