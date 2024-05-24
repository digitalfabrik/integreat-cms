import icalendar
import requests
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from ..abstract_base_model import AbstractBaseModel
from ..regions.region import Region


class ExternalCalendar(AbstractBaseModel):
    """
    Model for representing external calendars, from which events can be imported.
    """

    name = models.CharField(max_length=255, verbose_name=_("calendar name"), default="")
    region = models.ForeignKey(
        Region, on_delete=models.CASCADE, verbose_name=_("region")
    )
    url = models.CharField(max_length=255, verbose_name=_("URL"))
    import_filter_tag = models.CharField(
        max_length=255,
        blank=True,
        default=settings.EXTERNAL_CALENDAR_TAG,
        verbose_name=_(
            "The tag that events need to have to get imported (Leave blank to import all events)"
        ),
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
        """
        response = requests.get(self.url, timeout=60)
        if response.status_code != 200:
            raise IOError(
                f"Failed to load external calendar. Status code: {response.status_code}"
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
