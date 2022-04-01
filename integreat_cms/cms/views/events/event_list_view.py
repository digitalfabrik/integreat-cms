from datetime import date, time
import logging

from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...constants import (
    all_day,
    recurrence,
    status,
    events_time_range,
    translation_status,
)
from ...decorators import permission_required
from ...models import EventTranslation
from ...forms import EventFilterForm
from .event_context_mixin import EventContextMixin

from ....deepl_api.utils import DeepLApi

logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_event"), name="dispatch")
class EventListView(TemplateView, EventContextMixin):
    """
    View for listing events (either non-archived or archived events depending on
    :attr:`~integreat_cms.cms.views.events.event_list_view.EventListView.archived`)
    """

    #: Template for list of non-archived events
    template = "events/event_list.html"
    #: Template for list of archived events
    template_archived = "events/event_list_archived.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    extra_context = {
        "current_menu_item": "events",
        "WEBAPP_URL": settings.WEBAPP_URL,
        "PUBLIC": status.PUBLIC,
        "DEEPL_ENABLED": settings.DEEPL_ENABLED,
    }
    #: Whether or not to show archived events
    archived = False

    @property
    def template_name(self):
        """
        Select correct HTML template, depending on :attr:`~integreat_cms.cms.views.events.event_list_view.EventListView.archived` flag
        (see :class:`~django.views.generic.base.TemplateResponseMixin`)

        :return: Path to HTML template
        :rtype: str
        """
        return self.template_archived if self.archived else self.template

    # pylint: disable=too-many-branches
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements
    def get(self, request, *args, **kwargs):
        r"""
        Render events list for HTTP GET requests

        :param request: Object representing the user call
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        # current region
        region = request.region

        # current language
        language_slug = kwargs.get("language_slug")
        if language_slug:
            language = region.get_language_or_404(language_slug, only_active=True)
        elif region.default_language is not None:
            return redirect(
                "events",
                **{
                    "region_slug": region.slug,
                    "language_slug": region.default_language.slug,
                }
            )
        else:
            messages.error(
                request,
                _("Please create at least one language node before creating events."),
            )
            return redirect("language_tree", **{"region_slug": region.slug})

        if not request.user.has_perm("cms.change_event"):
            messages.warning(
                request, _("You don't have the permission to edit or create events.")
            )

        # all events of the current region in the current language
        events = region.events.filter(archived=self.archived)

        query = None

        # Filter events according to given filters, if any
        filter_data = kwargs.get("filter_data")
        if filter_data is not None:
            # Set data for filter form rendering
            event_filter_form = EventFilterForm(data=filter_data)
            poi = None
            if event_filter_form.is_valid():
                # Filter events by time range
                cleaned_time_range = event_filter_form.cleaned_data["events_time_range"]
                if (
                    set(cleaned_time_range) == set(events_time_range.ALL_EVENTS)
                    or len(cleaned_time_range) == 0
                ):
                    # Either post & upcoming or no checkboxes are checked => skip filtering
                    pass
                elif events_time_range.CUSTOM in cleaned_time_range:
                    # Filter events for their start and end
                    events = events.filter_upcoming(
                        event_filter_form.cleaned_data["date_from"] or date.min
                    ).filter(
                        end_date__lte=event_filter_form.cleaned_data["date_to"]
                        or date.max
                    )
                elif events_time_range.UPCOMING in cleaned_time_range:
                    # Only upcoming events
                    events = events.filter_upcoming()
                elif events_time_range.PAST in cleaned_time_range:
                    # Only past events
                    events = events.filter_completed()
                # Filter events for their location
                poi = region.pois.filter(
                    id=event_filter_form.cleaned_data["poi_id"]
                ).first()
                if poi is not None:
                    events = events.filter(location=poi)
                # Filter events for their all-day property
                if (
                    len(event_filter_form.cleaned_data["all_day"])
                    == len(all_day.CHOICES)
                    or len(event_filter_form.cleaned_data["all_day"]) == 0
                ):
                    # Either all or no checkboxes are checked => skip filtering
                    pass
                elif all_day.ALL_DAY in event_filter_form.cleaned_data["all_day"]:
                    # Filter for all-day events
                    events = events.filter(
                        start_time=time.min,
                        end_time=time.max.replace(second=0, microsecond=0),
                    )
                elif all_day.NOT_ALL_DAY in event_filter_form.cleaned_data["all_day"]:
                    # Exclude all-day events
                    events = events.exclude(
                        start_time=time.min,
                        end_time=time.max.replace(second=0, microsecond=0),
                    )
                # Filter events for recurrence
                if (
                    len(event_filter_form.cleaned_data["recurring"])
                    == len(recurrence.CHOICES)
                    or len(event_filter_form.cleaned_data["recurring"]) == 0
                ):
                    # Either all or no checkboxes are checked => skip filtering
                    pass
                elif (
                    recurrence.RECURRING in event_filter_form.cleaned_data["recurring"]
                ):
                    # Only recurring events
                    events = events.filter(recurrence_rule__isnull=False)
                elif (
                    recurrence.NOT_RECURRING
                    in event_filter_form.cleaned_data["recurring"]
                ):
                    # Only non-recurring events
                    events = events.filter(recurrence_rule__isnull=True)
                # Filter events by the search query
                query = event_filter_form.cleaned_data["query"]
                if query:
                    event_ids = EventTranslation.search(
                        region, language_slug, query
                    ).values("event__pk")
                    events = events.filter(pk__in=event_ids)
        else:
            # Show only upcoming events by default
            events = events.filter_upcoming()
            event_filter_form = EventFilterForm()
            event_filter_form.changed_data.clear()
            poi = None
        chunk_size = int(request.GET.get("size", settings.PER_PAGE))
        # for consistent pagination querysets should be ordered
        paginator = Paginator(
            events.prefetch_translations().order_by("start_date", "start_time"),
            chunk_size,
        )
        chunk = request.GET.get("page")
        event_chunk = paginator.get_page(chunk)

        # DeepL available

        if settings.DEEPL_ENABLED:
            deepl = DeepLApi()
            DEEPL_AVAILABLE = deepl.check_availability(request, language_slug)
        else:
            DEEPL_AVAILABLE = False

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
                "DEEPL_AVAILABLE": DEEPL_AVAILABLE,
            },
        )

    def post(self, request, *args, **kwargs):
        r"""
        Render event list with applied filters

        :param request: Object representing the user call
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        return self.get(request, *args, **kwargs, filter_data=request.POST)
