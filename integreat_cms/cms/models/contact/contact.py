from __future__ import annotations

import re
from functools import reduce
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.functional import cached_property, classproperty
from django.utils.translation import gettext_lazy as _
from linkcheck.models import Link

from ..abstract_base_model import AbstractBaseModel
from ..events.event_translation import EventTranslation
from ..pages.page_translation import PageTranslation
from ..pois.poi import POI
from ..pois.poi_translation import POITranslation
from ..regions.region import Region

if TYPE_CHECKING:
    from django.db.models.query import QuerySet


class Contact(AbstractBaseModel):
    """
    Data model representing a contact
    """

    point_of_contact_for = models.CharField(
        max_length=200, blank=True, verbose_name=_("point of contact for")
    )
    name = models.CharField(max_length=200, blank=True, verbose_name=_("name"))
    location = models.ForeignKey(
        POI,
        on_delete=models.PROTECT,
        verbose_name=_("location"),
        related_name="contacts",
    )
    email = models.EmailField(
        blank=True,
        verbose_name=_("email address"),
    )
    phone_number = models.CharField(
        max_length=250,
        blank=True,
        verbose_name=_("phone number"),
    )
    website = models.URLField(blank=True, max_length=250, verbose_name=_("website"))
    archived = models.BooleanField(
        default=False,
        verbose_name=_("archived"),
        help_text=_("Whether or not the location is read-only and hidden in the API."),
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name=_("modification date"),
    )
    created_date = models.DateTimeField(
        default=timezone.now, verbose_name=_("creation date")
    )

    @cached_property
    def region(self) -> Region:
        """
        Returns the region this contact belongs to

        :return: Region this contact belongs to
        """
        return self.location.region

    @classmethod
    def search(cls, region: Region, query: str) -> QuerySet:
        """
        Searches for all contacts which match the given `query` in their comment.
        :param region: The current region
        :param query: The query string used for filtering the contacts
        :return: A query for all matching objects
        """
        vector = SearchVector(
            "name",
            "email",
            "phone_number",
            "website",
            "point_of_contact_for",
        )
        query = SearchQuery(query)
        return (
            Contact.objects.filter(location__region=region, archived=False)
            .annotate(rank=SearchRank(vector, query))
            .order_by("-rank")
        )

    def __str__(self) -> str:
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``Contact object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the contact
        """
        location_name = str(self.location)
        additional_attribute = self.get_additional_attribute()
        return " ".join(part for part in [location_name, additional_attribute] if part)

    def get_additional_attribute(self) -> str:
        """
        This function determines which string is shown for the contact
        """

        if self.point_of_contact_for:
            return _("with point of contact for: {}").format(self.point_of_contact_for)

        if self.name:
            return _("with name: {}").format(self.name)

        if self.email:
            return _("with email: {}").format(self.email)

        if self.phone_number:
            return _("with phone number: {}").format(self.phone_number)

        if self.website:
            return _("with website: {}").format(self.website)

        return ""

    def get_repr(self) -> str:
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<Contact: Contact object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the contact
        """
        return f"<Contact (id: {self.id}, point of contact for: {self.point_of_contact_for}, name: {self.name}, region: {self.region.slug})>"

    @cached_property
    def get_repr_short(self) -> str:
        """
        Returns a short representation only contaiing the relevant data, no field names.

        :return: The short representation of the contact
        """
        point_of_contact_for = (
            f"{self.point_of_contact_for}: " if self.point_of_contact_for else ""
        )
        name = f"{self.name} " if self.name else ""
        details = [
            detail for detail in [self.email, self.phone_number, self.website] if detail
        ]
        details_repr = f"({', '.join(details)})" if details else ""

        return f"{point_of_contact_for}{name}{details_repr}".strip()

    @cached_property
    def referring_page_translations(self) -> QuerySet[PageTranslation]:
        """
        Returns a queryset containing all :class:`~integreat_cms.cms.models.pages.page_translation.PageTranslation` objects which reference this contact

        :return: all PageTranslation objects referencing this contact
        """
        from ...linklists import PageTranslationLinklist

        return PageTranslation.objects.filter(
            id__in=(
                Link.objects.filter(
                    url__url=self.full_url,
                    content_type=PageTranslationLinklist.content_type(),
                ).values_list("object_id", flat=True)
            ),
        )

    @cached_property
    def referring_poi_translations(self) -> QuerySet[POITranslation]:
        """
        Returns a queryset containing all :class:`~integreat_cms.cms.models.pois.poi_translation.POITranslation` objects which reference this contact

        :return: all POITranslation objects referencing this contact
        """
        from ...linklists import POITranslationLinklist

        return POITranslation.objects.filter(
            id__in=(
                Link.objects.filter(
                    url__url=self.full_url,
                    content_type=POITranslationLinklist.content_type(),
                ).values_list("object_id", flat=True)
            ),
        )

    @cached_property
    def referring_event_translations(self) -> QuerySet[EventTranslation]:
        """
        Returns a queryset containing all :class:`~integreat_cms.cms.models.events.event_translation.EventTranslation` objects which reference this contact

        :return: all EventTranslation objects referencing this contact
        """
        from ...linklists import EventTranslationLinklist

        return EventTranslation.objects.filter(
            id__in=(
                Link.objects.filter(
                    url__url=self.full_url,
                    content_type=EventTranslationLinklist.content_type(),
                ).values_list("object_id", flat=True)
            ),
        )

    def archive(self) -> None:
        """
        Archives the contact
        """
        self.archived = True
        self.save()

    def restore(self) -> None:
        """
        Restores the contact
        """
        self.archived = False
        self.save()

    def copy(self) -> None:
        """
        Copies the contact
        """
        # In order to create a new object set pk to None
        self.pk = None
        self.point_of_contact_for = self.point_of_contact_for + " " + _("(Copy)")
        self.save()

    @cached_property
    def url_prefix(self) -> str:
        """
        Generates the prefix of the url of the contact

        For information about the components of such an url,
        see :meth:`~integreat_cms.cms.models.contact.contact.Contact.get_absolute_url`

        :return: The prefix to the url
        """
        return "/" + "/".join(
            filter(
                None,
                [
                    self.location.region.slug,
                    self.url_infix,
                ],
            )
        )

    @cached_property
    def url_infix(self) -> str:
        """
        Generates the infix of the url of the contact

        For information about the components of such an url,
        see :meth:`~integreat_cms.cms.models.contact.contact.Contact.get_absolute_url`
        """
        return "contact/"

    @cached_property
    def base_link(self) -> str:
        """
        Generates the base link which is the whole url without id

        For information about the components of such an url,
        see :meth:`~integreat_cms.cms.models.contact.contact.Contact.get_absolute_url`

        :return: the base link of the content
        """
        if not self.id:
            return settings.BASE_URL + "/"
        return settings.BASE_URL + self.url_prefix

    def get_absolute_url(self) -> str:
        """
        Generates the absolute url of the contact

        Here is an example for demonstrating the components::

            https://integreat.app/augsburg/contact/42/
            |----------------------------------------|    full_url
                                 |-------------------|    get_absolute_url()
            |-------------------------------------|       base_link
                                 |----------------|       url_prefix
                                          |-------|       url_infix
                                                  |--|    id

        :return: The absolute url
        """
        return self.url_prefix + str(self.id) + "/"

    @cached_property
    def full_url(self) -> str:
        """
        This property returns the full url of this contact

        :return: The full url
        """
        # f"{settings.WEBAPP_URL}/{self.location.region.slug}/contact/{self.id}/"
        return settings.BASE_URL + self.get_absolute_url()

    class Meta:
        verbose_name = _("contact")
        default_related_name = "contact"
        verbose_name_plural = _("contacts")
        default_permissions = ("change", "delete", "view")
        ordering = ["name"]

        constraints = [
            models.UniqueConstraint(
                "location",
                condition=Q(point_of_contact_for=""),
                name="contact_singular_empty_point_of_contact_per_location",
                violation_error_message=_(
                    "Only one contact per location can have an empty point of contact."
                ),
            ),
            models.CheckConstraint(
                check=~Q(point_of_contact_for="")
                | ~Q(name="")
                | ~Q(email="")
                | ~Q(phone_number="")
                | ~Q(website=""),
                name="contact_non_empty",
                violation_error_message=_(
                    "One of the following fields must be filled: point of contact for, name, e-mail, phone number, website."
                ),
            ),
        ]
