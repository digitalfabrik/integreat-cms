import logging

from django.conf import settings
from django.utils import translation
from django.views.generic import TemplateView

from ...utils.filter_links import filter_links
from ..chat.chat_context_mixin import ChatContextMixin

logger = logging.getLogger(__name__)


class DashboardView(TemplateView, ChatContextMixin):
    """
    View for the region dashboard
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "dashboard/dashboard.html"

    def get_context_data(self, **kwargs):
        r"""
        Extend context by amount of links per link filter and blog urls

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The context dictionary
        :rtype: dict
        """
        context = super().get_context_data(**kwargs)
        # Link count
        _, count_dict = filter_links(kwargs.get("region_slug"))
        context.update(count_dict)
        # RSS FEED urls
        language_slug = translation.get_language()
        context.update(
            {
                "current_menu_item": "region_dashboard",
                "blog_url": settings.BLOG_URLS[language_slug],
                "feed_url": settings.RSS_FEED_URLS[language_slug],
            }
        )
        return context
