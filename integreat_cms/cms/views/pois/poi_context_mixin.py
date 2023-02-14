import logging

from django.utils.translation import gettext_lazy as _
from django.views.generic.base import ContextMixin

from ...constants import translation_status, weekdays
from ...models import POI

logger = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class POIContextMixin(ContextMixin):
    """
    This mixin provides extra context for language tree views
    """

    def get_context_data(self, **kwargs):
        r"""
        Returns a dictionary representing the template context
        (see :meth:`~django.views.generic.base.ContextMixin.get_context_data`).

        :param \**kwargs: The given keyword arguments
        :type \**kwargs: dict

        :return: The template context
        :rtype: dict
        """
        context = super().get_context_data(**kwargs)
        opening_hour_config_data = {
            "days": {
                "all": list(dict(weekdays.CHOICES).keys()),
                "workingDays": weekdays.WORKING_DAYS,
                "weekend": weekdays.WEEKEND,
            },
            "translations": {
                "weekdays": dict(weekdays.CHOICES),
                "openingHoursLabel": POI._meta.get_field(
                    "opening_hours"
                ).verbose_name.title(),
                "editWeekdayLabel": _("Edit opening hours for this weekday"),
                "editAllLabel": _("Edit all opening hours"),
                "editWorkingDaysLabel": _('Edit "Mo - Fr"'),
                "editWeekendLabel": _('Edit "Sa & Su"'),
                "closedLabel": _("Closed"),
                "openingTimeLabel": _("Opening time"),
                "closingTimeLabel": _("Closing time"),
                "allDayLabel": _("Open around the clock"),
                "selectText": _(
                    "Select the days for which the times selected below should apply"
                ),
                "saveText": _("Save"),
                "cancelText": _("Cancel"),
                "addMoreText": _("Add another time slot"),
                "removeTimeSlotText": _("Remove this time slot"),
                "errorOnlyLastSlotEmpty": _("Only the last time slot may be empty"),
                "errorLastSlotRequired": _(
                    "If the location is neither closed nor open all day, you have to specify at least one time slot"
                ),
                "errorClosingTimeMissing": _("Closing time is missing"),
                "errorOpeningTimeMissing": _("Opening time is missing"),
                "errorClosingTimeEarlier": _(
                    "Closing time is earlier than the opening time"
                ),
                "errorClosingTimeIdentical": _(
                    "Closing time is identical with the opening time"
                ),
                "errorOpeningTimeEarlier": _(
                    "Opening time is earlier than the closing time of the previous slot"
                ),
                "errorOpeningTimeIdentical": _(
                    "Opening time is identical with the closing time of the previous slot"
                ),
            },
        }
        context.update(
            {
                "translation_status": translation_status,
                "archive_dialog_title": _(
                    "Please confirm that you really want to archive this location"
                ),
                "archive_dialog_text": _(
                    "All translations of this location will also be archived."
                ),
                "restore_dialog_title": _(
                    "Please confirm that you really want to restore this location"
                ),
                "restore_dialog_text": _(
                    "All translations of this location will also be restored."
                ),
                "delete_dialog_title": _(
                    "Please confirm that you really want to delete this location"
                ),
                "delete_dialog_text": _(
                    "All translations of this location will also be deleted."
                ),
                "opening_hour_config_data": opening_hour_config_data,
            }
        )
        return context
