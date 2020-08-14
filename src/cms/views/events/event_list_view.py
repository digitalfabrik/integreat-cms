from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...decorators import region_permission_required
from ...models import Region
from ...forms.events import EventFilterForm


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
# pylint: disable=too-many-ancestors
class EventListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = "cms.view_events"
    raise_exception = True

    template = "events/event_list.html"
    template_archived = "events/event_list_archived.html"
    archived = False

    @property
    def template_name(self):
        return self.template_archived if self.archived else self.template

    def get(self, request, *args, **kwargs):
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

        event_filter_form = EventFilterForm()

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
            },
        )

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)
