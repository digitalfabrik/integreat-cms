import icalendar
import requests
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from integreat_cms.cms.models.abstract_base_model import AbstractBaseModel
from integreat_cms.cms.models.regions.region import Region


class ExternalCalendar(AbstractBaseModel):
    """
    Model for representing external calendars, from which events can be imported.
    """

    name = models.CharField(max_length=255, verbose_name=_("calendar name"), default="")
    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        verbose_name=_("region"),
        related_name="external_calendars",
    )
    url = models.URLField(max_length=250, verbose_name=_("URL"))

    import_filter_category = models.CharField(
        max_length=255,
        blank=True,
        default=settings.EXTERNAL_CALENDAR_CATEGORY,
        verbose_name=_(
            "The category that events need to have to get imported (Leave blank to import all events)",
        ),
    )
    errors = models.CharField(verbose_name=_("import errors"), default="", blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("creator"),
        help_text=_("The account that created this external calendar."),
    )
    last_changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="+",
        on_delete=models.SET_NULL,
        verbose_name=_("last changed by"),
        help_text=_("The account that was the last to change this external calendar."),
    )
    last_changed_on = models.DateTimeField(
        auto_now=True,
        verbose_name=_("last changed on"),
    )

    def __str__(self) -> str:
        """
        String representation of this model.
        :return: String that represents the region and the url.
        """
        return self.name

    def load_ical(self) -> icalendar.Calendar:
        """
        Loads the url and creates an icalendar
        :return: The Icalendar returned by the url
        :raises OSError: If the url cannot be loaded
        :raises ValueError: If the data are not valid icalendar format
        """
        response = requests.get(self.url, timeout=60)
        if response.status_code != 200:
            raise OSError(
                f"Failed to load external calendar. Status code: {response.status_code}",
            )
        return icalendar.Calendar.from_ical(response.content)

    def get_repr(self) -> str:
        """
        This overwrites the default Django ``__repr__()`` method

        :return: The canonical string representation of the external calendar
        """
        class_name = type(self).__name__
        return f"<{class_name} (url: {self.url})>"

    class Meta:
        #: The verbose name of the model
        verbose_name = _("external calendar")
        #: The plural verbose name of the model
        verbose_name_plural = _("external calendars")
        #: The default permissions for this model
        default_permissions = ("change", "delete", "view")
