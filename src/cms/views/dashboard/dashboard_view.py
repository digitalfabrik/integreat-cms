import html
from urllib.parse import urlparse
import feedparser

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import translation
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from backend.settings import RSS_FEED_URLS
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

        language_code = translation.get_language()
        feed = feedparser.parse(RSS_FEED_URLS[language_code])
        # select five most recent feeds
        feed["entries"] = feed["entries"][:5]
        # decode html entities like dash and split after line break
        for entry in feed["entries"]:
            entry["summary"] = html.unescape(entry["summary"]).split("\n")[0]
        domain = urlparse(RSS_FEED_URLS["home-page"]).netloc
        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                "feed": feed,
                "home_page": RSS_FEED_URLS["home-page"],
                "domain": domain,
            },
        )
