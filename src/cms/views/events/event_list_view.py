from datetime import date, time

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from backend.settings import PER_PAGE

from ...constants import all_day, recurrence
from ...decorators import region_permission_required
from ...models import Region
from ...forms import EventFilterForm
from .event_context_mixin import EventContextMixin


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
# pylint: disable=too-many-ancestors
class EventListView(
    LoginRequiredMixin, PermissionRequiredMixin, TemplateView, EventContextMixin
):
    """
    View for listing events (either non-archived or archived events depending on
    :attr:`~cms.views.events.event_list_view.EventListView.archived`)
    """

    #: Required permission of this view (see :class:`~django.contrib.auth.mixins.PermissionRequiredMixin`)
    permission_required = "cms.view_events"
    #: Whether or not an exception should be raised if the user is not logged in (see :class:`~django.contrib.auth.mixins.LoginRequiredMixin`)
    raise_exception = True
    #: Template for list of non-archived events
    template = "events/event_list.html"
    #: Template for list of archived events
    template_archived = "events/event_list_archived.html"
    #: Whether or not to show archived events
    archived = False

    @property
    def template_name(self):
        """
        Select correct HTML template, depending on :attr:`~cms.views.events.event_list_view.EventListView.archived` flag
        (see :class:`~django.views.generic.base.TemplateResponseMixin`)

        :return: Path to HTML template
        :rtype: str
        """
        return self.template_archived if self.archived else self.template

    # pylint: disable=too-many-branches
    def get(self, request, *args, **kwargs):
        """
        Render events list for HTTP GET requests

        :param request: Object representing the user call
        :type request: ~django.http.HttpRequest

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        # current region
        region = Region.get_current_region(request)

        # current language
        language_slug = kwargs.get("language_slug")
        if language_slug:
            language = region.languages.get(slug=language_slug)
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

        if not request.user.has_perm("cms.edit_events"):
            messages.warning(
                request, _("You don't have the permission to edit or create events.")
            )

        # all events of the current region in the current language
        events = region.events.filter(archived=self.archived)

        # Filter events according to given filters, if any
        filter_data = kwargs.get("filter_data")
        if filter_data is not None:
            # Set data for filter form rendering
            event_filter_form = EventFilterForm(data=filter_data)
            poi = None
            if event_filter_form.is_valid():
                poi = region.pois.filter(
                    id=event_filter_form.cleaned_data["poi_id"]
                ).first()
                # Filter events for their start and end
                events = events.filter(
                    start_date__gte=event_filter_form.cleaned_data["after_date"]
                    or date.min,
                    start_time__gte=event_filter_form.cleaned_data["after_time"]
                    or time.min,
                    end_date__lte=event_filter_form.cleaned_data["before_date"]
                    or date.max,
                    end_time__lte=event_filter_form.cleaned_data["before_time"]
                    or time.max,
                )
                # Filter events for their location
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
        else:
            event_filter_form = EventFilterForm()
            event_filter_form.changed_data.clear()
            poi = None
        # for consistent pagination querysets should be ordered
        paginator = Paginator(events.order_by("start_date", "start_time"), PER_PAGE)
        chunk = request.GET.get("chunk")
        event_chunk = paginator.get_page(chunk)
        context = self.get_context_data(**kwargs)
        return render(
            request,
            self.template_name,
            {
                **context,
                "current_menu_item": "events",
                "events": event_chunk,
                "archived_count": region.events.filter(archived=True).count(),
                "language": language,
                "languages": region.languages,
                "filter_form": event_filter_form,
                "filter_poi": poi,
            },
        )

    def post(self, request, *args, **kwargs):
        """
        Render event list with applied filters

        :param request: Object representing the user call
        :type request: ~django.http.HttpRequest

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        return self.get(request, *args, **kwargs, filter_data=request.POST)
