from django.db import models
from django.utils import timezone
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
        on_delete=models.SET_NULL,
        related_name="icon_organizations",
        blank=True,
        null=True,
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

    def __str__(self):
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``Organization object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the organization
        :rtype: str
        """
        return self.name

    def get_repr(self):
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<Organization: Organization object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the organization
        :rtype: str
        """
        return f"<Organization (id: {self.id}, slug: {self.slug}, region: {self.region.slug})>"

    @property
    def num_pages(self):
        """

        :return: the current number of maintained pages of an organization object
        :rtype: int
        """
        return self.pages.count()

    @property
    def num_members(self):
        """
        :return: the current number of members of an organization object
        :rtype: int
        """
        return self.members.count()

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
