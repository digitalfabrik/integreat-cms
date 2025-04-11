from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from linkcheck.models import Link

from ...utils.link_utils import fix_content_link_encoding
from ..abstract_base_model import AbstractBaseModel
from ..media.media_file import MediaFile
from ..regions.region import Region

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from django.db.models.query import QuerySet

    from ..users.user import User


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
        Region,
        on_delete=models.CASCADE,
        verbose_name=_("region"),
    )
    created_date = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("creation date"),
    )

    website = models.URLField(max_length=250, verbose_name=_("website"))
    archived = models.BooleanField(default=False, verbose_name=_("archived"))
    links = GenericRelation(Link, related_query_name="organization")

    @property
    def num_contents(self) -> int:
        """

        :return: the current number of maintained pages of an organization object
        """
        return self.pages.count() + self.pois.count()

    @property
    def num_members(self) -> int:
        """
        :return: the current number of members of an organization object
        """
        return self.members.count()

    @property
    def is_used(self) -> bool:
        """
        :return: whether this organization is used by another model
        """
        return self.pages.exists() or self.pois.exists() or self.members.exists()

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
                "organization_id": self.id,
            },
        )

    def replace_urls(
        self,
        urls_to_replace: dict[str, str],
        user: User | None = None,
        commit: bool = True,
    ) -> None:
        """
        Function to replace links that are in the translation and match the given keyword `search`
        """
        logger.debug("Replacing links of %r: %r by %r", self, urls_to_replace, user)
        self.website = urls_to_replace.get(self.website, self.website)
        self.website = fix_content_link_encoding(self.website)
        if commit:
            self.save()

    @classmethod
    def search(cls, region: Region, query: str) -> QuerySet:
        """
        Searches for all organizations which match the given `query` in their name.
        :param query: The query string used for filtering the organizations
        :return: A query for all matching objects
        """
        return cls.objects.filter(region=region, name__icontains=query)

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

    def delete(self, *args: list, **kwargs: dict) -> bool:
        r"""
        Deletes the organization

        :param \*args: The supplied arguments
        :param \**kwargs: The supplied keyword arguments
        """
        was_successful = False
        if not self.is_used:
            super().delete(*args, **kwargs)
            was_successful = True
        else:
            logger.debug(
                "Can't be deleted because this organization is used by a poi, page or user",
            )
        return was_successful

    def archive(self) -> bool:
        """
        Archives the organizations
        """
        was_successful = False
        if not self.is_used:
            self.archived = True
            self.save()
            was_successful = True
        else:
            logger.debug(
                "Can't be archived because this organization is used by a poi, page or user",
            )
        return was_successful

    def restore(self) -> None:
        """
        Restores the organization
        """
        self.archived = False
        self.save()

    @property
    def title(self) -> str:
        """
        This function return the name of organization. Alias for link list template.
        """
        return self.name

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
