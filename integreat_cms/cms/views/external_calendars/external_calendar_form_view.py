from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from integreat_cms.cms.decorators import permission_required
from integreat_cms.cms.forms import ExternalCalendarForm
from integreat_cms.cms.utils.external_calendar_utils import import_events

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest, HttpResponse

    from integreat_cms.cms.models import ExternalCalendar
    from integreat_cms.cms.utils.external_calendar_utils import ImportResult


logger = logging.getLogger(__name__)


@method_decorator(permission_required("cms.view_externalcalendar"), name="get")
@method_decorator(permission_required("cms.change_externalcalendar"), name="post")
class ExternalCalendarFormView(TemplateView):
    """
    Form view for new external calendars in a region.
    """

    template_name = "events/external_calendar_form.html"

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Render :class:`~integreat_cms.cms.forms.events.external_calendar_form.ExternalCalendarForm`

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """
        region = request.region
        external_calendar_instance = region.external_calendars.filter(
            id=kwargs.get("calendar_id"),
        ).first()
        external_calendar_form = ExternalCalendarForm(
            instance=external_calendar_instance,
            user=None,
        )
        return render(
            request,
            self.template_name,
            {
                "external_calendar_form": external_calendar_form,
                "current_menu_item": "external_calendar_list",
                "delete_dialog_title": _(
                    "Please confirm that you really want to delete this external calendar",
                ),
            },
        )

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        r"""
        Submit :class:`~integreat_cms.cms.forms.events.external_calendar_form.ExternalCalendarForm` and save :class:`~django.contrib.auth.models.events.ExternalCalendar` object

        :param request: The current request
        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        :return: The rendered template response
        """
        region = request.region
        external_calendar_instance = region.external_calendars.filter(
            id=kwargs.get("calendar_id"),
        ).first()
        external_calendar_form = ExternalCalendarForm(
            data=request.POST,
            instance=external_calendar_instance,
            user=request.user,
        )
        if not external_calendar_form.is_valid():
            external_calendar_form.add_error_messages(request)
        elif not external_calendar_form.has_changed():
            messages.info(request, _("No changes made"))

            import_result = import_events(external_calendar_form.instance, logger)
            self.show_import_messages(external_calendar_form.instance, import_result)

        else:
            external_calendar_form.instance.region = self.request.region
            external_calendar_form.save()
            if not external_calendar_instance:
                messages.success(
                    request,
                    _('External calendar "{}" was successfully created').format(
                        external_calendar_form.instance,
                    ),
                )
            else:
                messages.success(
                    request,
                    _('External calendar "{}" was successfully saved').format(
                        external_calendar_form.instance,
                    ),
                )

            import_result = import_events(external_calendar_form.instance, logger)
            self.show_import_messages(external_calendar_form.instance, import_result)

            return redirect(
                "edit_external_calendar",
                region_slug=self.request.region.slug,
                calendar_id=external_calendar_form.instance.id,
            )

        return render(
            request,
            self.template_name,
            {
                "external_calendar_form": external_calendar_form,
                "current_menu_item": "external_calendar_list",
            },
        )

    def show_import_messages(
        self,
        external_calendar_instance: ExternalCalendar,
        import_result: ImportResult,
    ) -> None:
        """
        This function shows the message after the import has been done

        :param external_calendar_instance: The instance of the external calendar
        :param import_result: The results of the import, either successes or errors
        """
        number_of_errors = import_result.number_of_errors
        number_of_successes = external_calendar_instance.events.count()

        if not number_of_successes and number_of_errors > 0:
            messages.error(
                self.request,
                _(
                    "No events have been successfully imported from this external calendar",
                ),
            )
        elif number_of_successes > 0 and number_of_errors > 0:
            messages.warning(
                self.request,
                _(
                    _(
                        "Could not import %d events of this external calendar (out of %d total). See the status for more information",
                    )
                    % (
                        number_of_errors,
                        number_of_errors + number_of_successes,
                    ),
                ),
            )
        else:
            messages.success(
                self.request,
                _("Successfully imported events from this external calendar"),
            )
