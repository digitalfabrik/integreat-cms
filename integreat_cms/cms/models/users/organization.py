from __future__ import annotations

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from ..abstract_base_model import AbstractBaseModel
from ..media.media_file import MediaFile
from ..regions.region import Region


class Organization(AbstractBaseModel):
    """
    Data model representing an organization
    """

    name = models.CharField(max_length=200, verbose_name=_("name"))
    slug = models.SlugField(
        max_length=200,
        unique=True,
        allow_unicode=True,
        verbose_name=_("slug"),
        help_text=_("Unique string identifier without spaces and special characters."),
    )

    icon = models.ForeignKey(
        MediaFile,
        verbose_name=_("logo"),
        on_delete=models.PROTECT,
        related_name="icon_organizations",
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name=_("modification date"),
    )

    region = models.ForeignKey(
        Region, on_delete=models.CASCADE, verbose_name=_("region")
    )
    created_date = models.DateTimeField(
        default=timezone.now, verbose_name=_("creation date")
    )

    website = models.URLField(max_length=250, verbose_name=_("website"))

    def __str__(self) -> str:
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``Organization object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the organization
        """
        return self.name

    def get_repr(self) -> str:
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<Organization: Organization object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the organization
        """
        return f"<Organization (id: {self.id}, slug: {self.slug}, region: {self.region.slug})>"

    @property
    def num_pages(self) -> int:
        """

        :return: the current number of maintained pages of an organization object
        """
        return self.pages.count()

    @property
    def num_members(self) -> int:
        """
        :return: the current number of members of an organization object
        """
        return self.members.count()

    @cached_property
    def backend_edit_link(self) -> str:
        """
        This function returns the absolute url to the edit form of this region

        :return: The url
        """
        return reverse(
            "edit_organization",
            kwargs={
                "region_slug": self.region.slug,
                "slug": self.slug,
            },
        )

    class Meta:
        #: The verbose name of the model
        verbose_name = _("organization")
        #: The name that will be used by default for the relation from a related object back to this one
        default_related_name = "organizations"
        #: The plural verbose name of the model
        verbose_name_plural = _("organizations")
        #: The default permissions for this model
        default_permissions = ("change", "delete", "view")
        #: The fields which are used to sort the returned objects of a QuerySet
        ordering = ["name"]
