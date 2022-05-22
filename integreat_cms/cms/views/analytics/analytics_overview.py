from django.views.generic import TemplateView


class AnalyticsView(TemplateView):
    """
    View to show all not-working links in the content.
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "analytics/analytics_overview.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    extra_context = {"current_menu_item": "analytics"}
