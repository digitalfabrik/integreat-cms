import logging

from django.views.generic import TemplateView

logger = logging.getLogger(__name__)


class AppSizeView(TemplateView):
    """
    View to calculate the current size of the content, that's been send via the API.
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "analytics/app_size.html"

    def get_context_data(self, **kwargs):
        r"""
        Extend context by app size

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The context dictionary
        :rtype: dict
        """
        context = super().get_context_data(**kwargs)

        # TODO: Implement correct calculation.
        app_size_total = 0

        context.update({"current_menu_item": "app_size", "app_size": app_size_total})
        return context
