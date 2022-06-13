from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from linkcheck.models import Link

from ..abstract_content_translation import AbstractContentTranslation
from ..decorators import modify_fields


@modify_fields(
    slug={"verbose_name": _("event link")},
    title={"verbose_name": _("title of the event")},
    content={"verbose_name": _("description")},
)
class EventTranslation(AbstractContentTranslation):
    """
    Data model representing an event translation
    """

    event = models.ForeignKey(
        "cms.Event",
        on_delete=models.CASCADE,
        related_name="translations",
        verbose_name=_("event"),
    )
    links = GenericRelation(Link, related_query_name="event_translation")

    @cached_property
    def foreign_object(self):
        """
        This property is an alias of the event foreign key and is needed to generalize the :mod:`~integreat_cms.cms.utils.slug_utils`
        for all content types

        :return: The event to which the translation belongs
        :rtype: ~integreat_cms.cms.models.events.event.Event
        """
        return self.event

    @staticmethod
    def foreign_field():
        """
        Returns the string "event" which ist the field name of the reference to the event which the translation belongs to

        :return: The foreign field name
        :rtype: str
        """
        return "event"

    @cached_property
    def url_infix(self):
        """
        Returns the string "events" which is the infix of the url of  the event translation object
        Generates the infix of the url of the event translation object

        For information about the components of such an url,
        see :meth:`~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation.get_absolute_url`

        :return: The infix of the url
        :rtype: str
        """
        return "events"

    @cached_property
    def backend_edit_link(self):
        """
        This function returns the absolute url to the editor for this translation

        :return: The url
        :rtype: str
        """
        return reverse(
            "edit_event",
            kwargs={
                "event_id": self.event.id,
                "language_slug": self.language.slug,
                "region_slug": self.event.region.slug,
            },
        )

    class Meta:
        #: The verbose name of the model
        verbose_name = _("event translation")
        #: The plural verbose name of the model
        verbose_name_plural = _("event translations")
        #: The name that will be used by default for the relation from a related object back to this one
        default_related_name = "event_translations"
        #: The default permissions for this model
        default_permissions = ()
        #: The fields which are used to sort the returned objects of a QuerySet
        ordering = ["event__pk", "language__pk", "-version"]
        #: A list of database constraints for this model
        constraints = [
            models.UniqueConstraint(
                fields=["event", "language", "version"],
                name="%(class)s_unique_version",
            ),
        ]
