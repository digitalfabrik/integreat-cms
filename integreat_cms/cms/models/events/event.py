from __future__ import annotations

from datetime import datetime, time
from typing import TYPE_CHECKING

from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from linkcheck.models import Link

from ...constants import status
from ...utils.slug_utils import generate_unique_slug
from ..abstract_content_model import AbstractContentModel, ContentQuerySet
from ..media.media_file import MediaFile
from ..pois.poi import POI
from .event_translation import EventTranslation
from .recurrence_rule import RecurrenceRule

if TYPE_CHECKING:
    from datetime import date

    from django.db.models.base import ModelBase

    from ...utils.slug_utils import SlugKwargs
    from ..users.user import User


class EventQuerySet(ContentQuerySet):
    """
    Custom QuerySet to facilitate the filtering by date while taking recurring events into account.
    """

    def filter_upcoming(self, from_date: datetime | None = None) -> EventQuerySet:
        """
        Filter all events that take place after the given date. This is, per definition, if at least one of the
        following conditions is true:

            * The end date of the event is the given date or later
            * The event is indefinitely recurring
            * The event is recurring and the recurrence end date is the given date or later

        :param from_date: The date which should be used for filtering, defaults to the current date
        :return: The Queryset of events after the given date
        """
        from_date = from_date or timezone.now().date()
        return self.filter(
            Q(end__gte=from_date)
            | Q(
                recurrence_rule__isnull=False,
                recurrence_rule__recurrence_end_date__isnull=True,
            )
            | Q(
                recurrence_rule__isnull=False,
                recurrence_rule__recurrence_end_date__gte=from_date,
            )
        )

    def filter_completed(self, to_date: date | None = None) -> EventQuerySet:
        """
        Filter all events that are not ongoing and don't have any occurrences in the future. This is, per definition, if
        at least one of the following conditions is true:

            * The event is non-recurring and the end date of the event is before the given date
            * The event is recurring and the recurrence end date is before the given date

        :param to_date: The date which should be used for filtering, defaults to the current date
        :return: The Queryset of events before the given date
        """
        to_date = to_date or timezone.now().date()
        return self.filter(
            Q(recurrence_rule__isnull=True, end__lt=to_date)
            | Q(
                recurrence_rule__isnull=False,
                recurrence_rule__recurrence_end_date__lt=to_date,
            )
        )


class Event(AbstractContentModel):
    """
    Data model representing an event.
    Can be directly imported from :mod:`~integreat_cms.cms.models`.
    """

    location = models.ForeignKey(
        POI,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        verbose_name=_("location"),
    )
    start = models.DateTimeField(verbose_name=_("start"))
    end = models.DateTimeField(verbose_name=_("end"))
    #: If the event is recurring, the recurrence rule contains all necessary information on the frequency, interval etc.
    #: which is needed to calculate the single instances of a recurring event
    recurrence_rule = models.OneToOneField(
        RecurrenceRule,
        null=True,
        on_delete=models.SET_NULL,
        related_name="event",
        verbose_name=_("recurrence rule"),
    )
    icon = models.ForeignKey(
        MediaFile,
        verbose_name=_("icon"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    archived = models.BooleanField(default=False, verbose_name=_("archived"))

    #: The default manager
    objects = EventQuerySet.as_manager()

    @property
    def fallback_translations_enabled(self) -> bool:
        """
        Whether translations should be returned in the default language if they do not exist

        :return: Whether fallback translations are enabled
        """
        return self.region.fallback_translations_enabled

    @staticmethod
    def get_translation_model() -> ModelBase:
        """
        Returns the translation model of this content model

        :return: The class of translations
        """
        return EventTranslation

    @cached_property
    def is_recurring(self) -> bool:
        """
        This property checks if the event has a recurrence rule and thereby determines, whether the event is recurring.

        :return: Whether the event is recurring or not
        """
        return bool(self.recurrence_rule)

    @cached_property
    def is_past(self) -> bool:
        """
        This property checks whether an event lies in the past, including potential future recurrences.

        :return: Whether event lies in the past
        """
        now = timezone.now()
        duration = self.end_local - self.start_local
        future_recurrence = (
            self.is_recurring
            and self.recurrence_rule.to_ical_rrule().after(now - duration, True)
        )
        return self.end_local.date() < now.date() and not future_recurrence

    @cached_property
    def is_all_day(self) -> bool:
        """
        This property checks whether an event takes place the whole day by checking if start time is minimal and end
        time is maximal.

        :return: Whether event takes place all day
        """
        return (
            self.start_local.time() == time.min
            and self.end_local.time() == time.max.replace(second=0, microsecond=0)
        )

    @cached_property
    def timezone(self) -> str:
        """
        The timezone of this event's region

        :return: The timezone of this event
        """
        return self.region.timezone

    @cached_property
    def start_local(self) -> datetime:
        """
        Convert the start to local time

        :return: The start of the event in local time
        """
        timezone.activate(self.timezone)
        return timezone.localtime(self.start)

    @cached_property
    def end_local(self) -> datetime:
        """
        Convert the end to local time

        :return: The end of the event in local time
        """
        # Activate the timezone of the event's region
        timezone.activate(self.timezone)
        return timezone.localtime(self.end)

    @cached_property
    def has_location(self) -> bool:
        """
        This property checks whether the event has a physical location (:class:`~integreat_cms.cms.models.pois.poi.POI`).

        :return: Whether event has a physical location
        """
        return bool(self.location)

    def get_occurrences(self, start: datetime, end: datetime) -> list[datetime]:
        """
        Get occurrences of the event that overlap with ``[start, end]``.
        Expects ``start < end``.

        :param start: the begin of the requested interval.
        :param end: the end of the requested interval.
        :return: start datetimes of occurrences of the event that are in the given timeframe
        """
        event_start = self.start
        event_end = self.end
        if self.is_recurring is not None:
            return self.recurrence_rule.to_ical_rrule().between(start, end)
        return (
            [event_start]
            if start <= event_start <= end or start <= event_end <= end
            else []
        )

    def copy(self, user: User) -> Event:
        """
        This method creates a copy of this event and all of its translations.
        This method saves the new event.

        :param user: The user who initiated this copy
        :return: A copy of this event
        """
        # save all translations on the original object, so that they can be copied later
        translations = list(self.translations.all())

        # Clear the own recurrence rule.
        # If the own recurrence rule would not be cleared, django would throw an
        # error that the recurrence rule is not unique (because it would belong to both
        # the cloned and the new object)
        if recurrence_rule := self.recurrence_rule:
            # copy the recurrence rule, if it exists
            recurrence_rule.pk = None
            recurrence_rule.save()
            self.recurrence_rule = recurrence_rule

        # create the copied event
        self.pk = None
        self.save()

        copy_translation = _("copy")
        # Create new translations for this event
        for translation in translations:
            translation.pk = None
            translation.event = self
            translation.status = status.DRAFT
            translation.title = f"{translation.title} ({copy_translation})"
            kwargs: SlugKwargs = {
                "slug": translation.slug,
                "manager": type(translation).objects,
                "object_instance": translation,
                "foreign_model": "event",
                "region": self.region,
                "language": translation.language,
            }
            translation.slug = generate_unique_slug(**kwargs)
            translation.currently_in_translation = False
            translation.creator = user
            translation.save()

        return self

    def archive(self) -> None:
        """
        Archives the event and removes all links of this event from the linkchecker
        """
        self.archived = True
        self.save()

        # Delete related link objects as they are no longer required
        Link.objects.filter(event_translation__event=self).delete()

    def restore(self) -> None:
        """
        Restores the event and adds all links of this event back
        """
        self.archived = False
        self.save()

        # Restore related link objects
        for translation in self.translations.distinct("event__pk", "language__pk"):
            # The post_save signal will create link objects from the content
            translation.save(update_timestamp=False)

    class Meta:
        #: The verbose name of the model
        verbose_name = _("event")
        #: The plural verbose name of the model
        verbose_name_plural = _("events")
        #: The name that will be used by default for the relation from a related object back to this one
        default_related_name = "events"
        #: The fields which are used to sort the returned objects of a QuerySet
        ordering = ["start"]
        #: The default permissions for this model
        default_permissions = ("change", "delete", "view")
        #: The custom permissions for this model
        permissions = (("publish_event", "Can publish events"),)
