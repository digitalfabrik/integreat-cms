from django.utils.translation import gettext_lazy as _

from integreat_cms.cms.forms.pois.poi_form import POIForm
from integreat_cms.cms.models.contact.contact import Contact

from ...constants import weekdays
from ...models import POI


def get_open_hour_config_data(
    related_class: type[POIForm] | type[Contact], can_change_location: bool
) -> dict:
    use_office_hours = related_class == Contact
    if use_office_hours:
        edit_label = _("Edit office hours for this weekday")
        edit_all_label = _("Edit all office hours")
        model_verbose_name = Contact._meta.get_field(
            "opening_hours",
        ).verbose_name.title()
        openingTimeLabel = _("start time")
        closingTimeLabel = _("end time")
    else:
        edit_label = _("Edit opening hours for this weekday")
        edit_all_label = _("Edit all opening hours")
        model_verbose_name = POI._meta.get_field(
            "opening_hours",
        ).verbose_name.title()
        openingTimeLabel = _("Opening time")
        closingTimeLabel = _("Closing time")

    return {
        "days": {
            "all": list(dict(weekdays.CHOICES).keys()),
            "workingDays": weekdays.WORKING_DAYS,
            "weekend": weekdays.WEEKEND,
        },
        "translations": {
            "weekdays": dict(weekdays.CHOICES),
            "openingHoursLabel": model_verbose_name,
            "editWeekdayLabel": edit_label,
            "editAllLabel": edit_all_label,
            "editWorkingDaysLabel": _('Edit "Mo - Fr"'),
            "editWeekendLabel": _('Edit "Sa & Su"'),
            "closedLabel": _("Closed"),
            "openingTimeLabel": openingTimeLabel,
            "closingTimeLabel": closingTimeLabel,
            "allDayLabel": _("Open around the clock"),
            "appointmentOnlyLabel": _("By prior appointment only"),
            "selectText": _(
                "Select the days for which the times selected below should apply",
            ),
            "saveText": _("Save"),
            "cancelText": _("Cancel"),
            "addMoreText": _("Add another time slot"),
            "removeTimeSlotText": _("Remove this time slot"),
            "errorOnlyLastSlotEmpty": _("Only the last time slot may be empty"),
            "errorLastSlotRequired": _(
                "If the location is neither closed nor open all day, you have to specify at least one time slot",
            ),
            "errorClosingTimeMissing": _("Closing time is missing"),
            "errorOpeningTimeMissing": _("Opening time is missing"),
            "errorClosingTimeEarlier": _(
                "Closing time is earlier than the opening time",
            ),
            "errorClosingTimeIdentical": _(
                "Closing time is identical with the opening time",
            ),
            "errorOpeningTimeEarlier": _(
                "Opening time is earlier than the closing time of the previous slot",
            ),
            "errorOpeningTimeIdentical": _(
                "Opening time is identical with the closing time of the previous slot",
            ),
        },
        "canChangeLocation": can_change_location,
    }
