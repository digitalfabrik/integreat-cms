from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from ...decorators import permission_required
from ...forms import ObjectSearchForm
from ...models import PushNotificationTranslation

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_pushnotification"), name="dispatch")
class PushNotificationListView(TemplateView):
    """
    Class that handles HTTP GET requests for listing push notifications
    """

    #: If true, shows the template push notification list
    templates = False
    #: The template to render if templates is False
    template = "push_notifications/push_notification_list.html"
    #: The template to render if templates is True
    template_templates = "push_notifications/push_notification_template_list.html"

    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    extra_context = {"current_menu_item": "push_notifications"}

    @property
    def template_name(self) -> str:
        """
        Select correct HTML template, depending on :attr:`~integreat_cms.cms.views.push_notifications.push_notification_list_view.PushNotificationListView.templates` flag
        (see :class:`~django.views.generic.base.TemplateResponseMixin`)

        :return: Path to HTML template
        """

        return self.template_templates if self.templates else self.template

    # pylint: disable=too-many-locals
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Create a list that shows existing push notifications and translations

        :param request: Object representing the user call
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """

        # current region
        region = request.region

        if not settings.FCM_ENABLED:
            messages.error(
                request,
                _("Push notifications are disabled."),
            )
            return redirect("dashboard", **{"region_slug": region.slug})

        if not region.push_notifications_enabled:
            messages.error(
                request,
                _("Push notifications are disabled in this region."),
            )
            return redirect("dashboard", **{"region_slug": region.slug})

        # current language
        if language_slug := kwargs.get("language_slug"):
            language = region.get_language_or_404(language_slug, only_active=True)
        elif region.default_language:
            return redirect(
                "push_notifications",
                **{
                    "region_slug": region.slug,
                    "language_slug": region.default_language.slug,
                },
            )
        else:
            messages.error(
                request,
                _(
                    "Please create at least one language node before creating push notifications."
                ),
            )
            return redirect(
                "languagetreenodes",
                **{
                    "region_slug": region.slug,
                },
            )

        push_notifications = region.push_notifications.filter(
            is_template=self.templates
        )
        query = None

        search_data = kwargs.get("search_data")
        search_form = ObjectSearchForm(search_data)
        if search_form.is_valid():
            query = search_form.cleaned_data["query"]
            push_notification_keys = PushNotificationTranslation.search(
                region, language_slug, query
            ).values("push_notification__pk")
            push_notifications = push_notifications.filter(
                pk__in=push_notification_keys
            )

        chunk_size = int(request.GET.get("size", settings.PER_PAGE))
        # for consistent pagination querysets should be ordered
        paginator = Paginator(push_notifications, chunk_size)
        chunk = request.GET.get("page")
        push_notifications_chunk = paginator.get_page(chunk)
        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "push_notifications": push_notifications_chunk,
                "language": language,
                "languages": region.active_languages,
                "region_slug": region.slug,
                "search_query": query,
            },
        )

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Apply the query and filter the rendered push notifications

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """
        return self.get(request, *args, **kwargs, search_data=request.POST)
