import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import translation
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from ...decorators import region_permission_required
from ...utils.filter_links import filter_links
from ..chat.chat_context_mixin import ChatContextMixin

logger = logging.getLogger(__name__)


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
class DashboardView(TemplateView, ChatContextMixin):
    """
    View for the region dashboard
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "dashboard/dashboard.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    extra_context = {"current_menu_item": "region_dashboard"}

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

    def get(self, request, *args, **kwargs):
        r"""
        Render the region dashboard

        :param request: Object representing the user call
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        # RSS FEED
        language_slug = translation.get_language()

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "blog_url": settings.BLOG_URLS[language_slug],
                "feed_url": settings.RSS_FEED_URLS[language_slug],
            },
        )
