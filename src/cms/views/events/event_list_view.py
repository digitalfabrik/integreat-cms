from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...decorators import region_permission_required
from ...models import Language, Region, Event


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
        region_slug = kwargs.get("region_slug")
        region = Region.objects.get(slug=region_slug)

        # current language
        language_code = kwargs.get("language_code", None)
        if language_code is not None:
            language = Language.objects.get(code=language_code)
        elif region.default_language is not None:
            return redirect(
                "events",
                **{
                    "region_slug": region_slug,
                    "language_code": region.default_language.code,
                }
            )
        else:
            messages.error(
                request,
                _("Please create at least one language node before creating events."),
            )
            return redirect("language_tree", **{"region_slug": region_slug})

        if not request.user.has_perm("cms.edit_events"):
            messages.warning(
                request, _("You don't have the permission to edit or create events.")
            )

        # all events of the current region in the current language
        events = Event.get_list(region_slug, archived=self.archived)

        # all other languages of current region
        languages = region.languages

        return render(
            request,
            self.template_name,
            {
                "current_menu_item": "events",
                "events": events,
                "archived_count": Event.archived_count(region_slug),
                "language": language,
                "languages": languages,
            },
        )
