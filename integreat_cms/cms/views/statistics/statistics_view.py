"""Views related to the statistics module"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from integreat_cms.cms.constants import language_color

from ...decorators import permission_required
from ...forms import StatisticsFilterForm

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponseRedirect

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_statistics"), name="dispatch")
class AnalyticsView(TemplateView):
    """
    View for the statistics overview.
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "statistics/statistics_overview.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    extra_context = {"current_menu_item": "statistics"}

    def get(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseRedirect:
        r"""
        Render statistics of access numbers tracked by Matomo

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """
        region = request.region
        default_language = region.default_language
        languages = region.active_languages

        if not region.statistics_enabled:
            messages.error(request, _("Statistics are not enabled for this region."))
            return redirect(
                "dashboard",
                **{
                    "region_slug": region.slug,
                },
            )

        form = StatisticsFilterForm()

        page_queryset = region.pages.filter(lft=1)

        # Cache tree structure to reduce database queries
        pages = (
            page_queryset.prefetch_major_translations()
            .prefetch_related("mirroring_pages")
            .cache_tree(archived=False)
        )

        show_page_based_statistics = (
            request.user.has_perm("cms.test_beta_features")
            or region.slug in settings.PILOT_REGIONS_PAGE_BASED_STATISTICS
        )

        access_legends = {
            _("Phone App Accesses"): language_color.OFFLINE_ACCESS,
            _("WebApp Accesses"): language_color.WEB_APP_ACCESS,
            _("Total Accesses"): language_color.TOTAL_ACCESS,
        }

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "form": form,
                "pages": pages,
                "region": region,
                "language": default_language,
                "languages": languages,
                "access_legends": access_legends,
                "is_statistics": True,
                "show_page_based_statistics": show_page_based_statistics,
            },
        )
