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

from ...constants import translation_status
from ...decorators import permission_required
from ...forms import EventFilterForm
from ...models import EventTranslation
from ..mixins import MachineTranslationContextMixin
from .event_context_mixin import EventContextMixin

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_event"), name="dispatch")
class EventListView(TemplateView, EventContextMixin, MachineTranslationContextMixin):
    """
    View for listing events (either non-archived or archived events depending on
    :attr:`~integreat_cms.cms.views.events.event_list_view.EventListView.archived`)
    """

    #: Template for list of non-archived events
    template = "events/event_list.html"
    #: Template for list of archived events
    template_archived = "events/event_list_archived.html"
    #: Whether or not to show archived events
    archived = False
    #: The translation model of this list view (used to determine whether machine translations are permitted)
    translation_model = EventTranslation

    @property
    def template_name(self) -> str:
        """
        Select correct HTML template, depending on :attr:`~integreat_cms.cms.views.events.event_list_view.EventListView.archived` flag
        (see :class:`~django.views.generic.base.TemplateResponseMixin`)

        :return: Path to HTML template
        """
        return self.template_archived if self.archived else self.template

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Render events list for HTTP GET requests

        :param request: Object representing the user call
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """
        # current region
        region = request.region

        # current language
        if language_slug := kwargs.get("language_slug"):
            language = region.get_language_or_404(language_slug, only_active=True)
        elif region.default_language is not None:
            return redirect(
                "events",
                **{
                    "region_slug": region.slug,
                    "language_slug": region.default_language.slug,
                },
            )
        else:
            messages.error(
                request,
                _("Please create at least one language node before creating events."),
            )
            return redirect("languagetreenodes", **{"region_slug": region.slug})

        if not request.user.has_perm("cms.change_event"):
            messages.warning(
                request, _("You don't have the permission to edit or create events.")
            )

        # all events of the current region in the current language
        events = region.events.filter(archived=self.archived)

        # Filter events according to given filters, if any
        event_filter_form = EventFilterForm(data=request.GET)
        events, poi, query = event_filter_form.apply(events, region, language_slug)
        chunk_size = int(request.GET.get("size", settings.PER_PAGE))
        # for consistent pagination querysets should be ordered
        paginator = Paginator(
            events.prefetch_translations().order_by("start"),
            chunk_size,
        )
        chunk = request.GET.get("page")
        event_chunk = paginator.get_page(chunk)

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "events": event_chunk,
                "archived_count": region.events.filter(archived=True).count(),
                "language": language,
                "languages": region.active_languages,
                "filter_form": event_filter_form,
                "filter_poi": poi,
                "translation_status": translation_status,
                "search_query": query,
                "source_language": region.get_source_language(language.slug),
                "content_type": "events",
            },
        )
