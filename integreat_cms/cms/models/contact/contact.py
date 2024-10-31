from django.db import models
from django.db.models import Q
from django.db.utils import DataError
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from ..abstract_base_model import AbstractBaseModel
from ..fields.truncating_char_field import TruncatingCharField
from ..pois.poi import POI
from ..regions.region import Region


class Contact(AbstractBaseModel):
    """
    Data model representing a contact
    """

    point_of_contact_for = TruncatingCharField(
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

    def label_in_reference_list(self) -> str:
        """
        This function returns a display name of this contact for the poi contacts list
        """

        label = (
            _("General contact information")
            if not self.point_of_contact_for
            else f"{self.point_of_contact_for} {self.name}"
        )
        if self.archived:
            label += " (⚠ " + gettext("Archived") + ")"

        return label

    def get_repr(self) -> str:
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<Contact: Contact object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the contact
        """
        return f"<Contact (id: {self.id}, point of contact for: {self.point_of_contact_for}, name: {self.name}, region: {self.region.slug})>"

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
        self.pk = None
        self.point_of_contact_for = self.point_of_contact_for + " " + _("(Copy)")
        self.save()

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
