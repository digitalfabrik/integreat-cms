"""
Contains a class for handling requests to render the events list
"""
from datetime import date, time

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...constants import all_day, recurrence
from ...decorators import region_permission_required
from ...models import Region
from ...forms.events import EventFilterForm


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
# pylint: disable=too-many-ancestors
class EventListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """
    Class for rendering the events list
    """

    permission_required = "cms.view_events"
    raise_exception = True

    template = "events/event_list.html"
    template_archived = "events/event_list_archived.html"
    archived = False

    @property
    def template_name(self):
        """
        Select correct HTML template, depending on archived state

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

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        # current region
        region = Region.get_current_region(request)

        # current language
        language_code = kwargs.get("language_code")
        if language_code:
            language = region.languages.get(code=language_code)
        elif region.default_language is not None:
            return redirect(
                "events",
                **{
                    "region_slug": region.slug,
                    "language_code": region.default_language.code,
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

        return render(
            request,
            self.template_name,
            {
                "current_menu_item": "events",
                "events": events,
                "archived_count": region.events.filter(archived=True).count(),
                "language": language,
                "languages": region.languages,
                "filter_form": event_filter_form,
                "filter_poi": poi,
            },
        )

    def post(self, request, *args, **kwargs):
        """
        Render events list for HTTP POST requests

        :param request: Object representing the user call
        :type request: ~django.http.HttpRequest

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        return self.get(request, *args, **kwargs, filter_data=request.POST)
