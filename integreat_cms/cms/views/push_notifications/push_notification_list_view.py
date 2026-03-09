from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from ...decorators import permission_required
from ...models import PushNotification
from ..mixins import FilterSortMixin, PaginationMixin

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse

    from integreat_cms.cms.models.regions.region import Region

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_pushnotification"), name="dispatch")
class PushNotificationListView(TemplateView, FilterSortMixin, PaginationMixin):
    """
    Class that handles HTTP GET requests for listing push notifications
    """

    #: If true, shows the template push notification list
    not_sent = False
    archived = False

    template = "push_notifications/push_notification_list.html"

    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    extra_context = {"current_menu_item": "push_notifications"}
    model = PushNotification

    def count_archived_push_notifications(self, region: Region) -> int:
        """
        Counts the amount of archived push notifications
        """
        return PushNotification.objects.filter(
            regions=region,
            archived=True,
        ).count()

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
                    "Please create at least one language node before creating push notifications.",
                ),
            )
            return redirect(
                "languagetreenodes",
                **{
                    "region_slug": region.slug,
                },
            )

        push_notifications = region.push_notifications.filter(
            archived=self.archived,
        )

        if self.not_sent:
            push_notifications = push_notifications.filter(sent_date__isnull=True)
        search_query = request.GET.get("search_query") or None

        push_notifications = self.get_filtered_sorted_queryset(push_notifications)
        push_notifications_chunk = self.paginate_queryset(push_notifications)

        archived_count = self.count_archived_push_notifications(region)
        return render(
            request,
            self.template,
            {
                **self.get_context_data(**kwargs),
                "push_notifications": push_notifications_chunk,
                "language": language,
                "languages": region.active_languages,
                "region_slug": region.slug,
                "search_query": search_query,
                "is_archived": self.archived,
                "archived_count": archived_count,
                "not_sent": self.not_sent,
            },
        )
