from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from linkcheck.models import Link
from lxml.html import Element

if TYPE_CHECKING:
    from typing import Literal
    from ...models import Event

from ...utils.tinymce_icon_utils import get_icon_html
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
    def foreign_object(self) -> Event:
        """
        This property is an alias of the event foreign key and is needed to generalize the :mod:`~integreat_cms.cms.utils.slug_utils`
        for all content types

        :return: The event to which the translation belongs
        """
        return self.event

    @staticmethod
    def foreign_field() -> Literal["event"]:
        """
        Returns the string "event" which ist the field name of the reference to the event which the translation belongs to

        :return: The foreign field name
        """
        return "event"

    @cached_property
    def url_infix(self) -> Literal["events"]:
        """
        Returns the string "events" which is the infix of the url of  the event translation object
        Generates the infix of the url of the event translation object

        For information about the components of such an url,
        see :meth:`~integreat_cms.cms.models.abstract_content_translation.AbstractContentTranslation.get_absolute_url`

        :return: The infix of the url
        """
        return "events"

    @cached_property
    def backend_edit_link(self) -> str:
        """
        This function returns the absolute url to the editor for this translation

        :return: The url
        """
        return reverse(
            "edit_event",
            kwargs={
                "event_id": self.event.id,
                "language_slug": self.language.slug,
                "region_slug": self.event.region.slug,
            },
        )

    @cached_property
    def link_title(self) -> Element | str:
        """
        This property returns the html that should be used as a title for a link to this translation

        :return: The link content
        """
        img = get_icon_html("clock")

        if icon := self.event.icon:
            if thumbnail := icon.thumbnail_url:
                img = Element("img")
                img.set("style", "height:15px;")
                img.set("src", thumbnail)

        img.tail = self.title
        return img

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
