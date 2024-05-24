from __future__ import annotations

from typing import TYPE_CHECKING

from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from ...decorators import permission_required
from ...models.events.external_calendar import ExternalCalendar

if TYPE_CHECKING:
    from typing import Any


@method_decorator(permission_required("auth.change_external_calendar"), name="get")
class ExternalCalendarList(TemplateView):
    """
    View for external calendars in regions.
    """

    template_name = "events/external_calendar_list.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        r"""
        Get external calendar list context data

        :return: The context dictionary
        """
        context = super().get_context_data(**kwargs)
        external_calendars = ExternalCalendar.objects.filter(region=self.request.region)
        context.update(
            {
                "current_menu_item": "external_calendar_list",
                "external_calendars": external_calendars,
                "delete_dialog_title": _(
                    "Please confirm that you really want to delete this calendar"
                ),
            }
        )
        return context
