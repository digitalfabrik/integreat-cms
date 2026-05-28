from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.formats import localize
from django.utils.translation import gettext_lazy as _

from ...search.search_fields import DIRECTORY_SEARCH_FIELDS
from ..abstract_base_model import AbstractBaseModel
from ..mixins import SearchSuggestMixin
from ..regions.region import Region

if TYPE_CHECKING:
    from typing import Any

    from django.db.models.query import QuerySet


class Directory(AbstractBaseModel, SearchSuggestMixin):
    """
    Model representing a directory containing documents. This is only a virtual directory and does not necessarily
    exist on the actual file system. Each directory is tied to a region.
    """

    search_fields = DIRECTORY_SEARCH_FIELDS
    region_filter_field = "region"
    archived_filter_field = None

    @classmethod
    def get_suggest_queryset(
        cls,
        region: Region | None = None,
        archived: bool = False,  # noqa: ARG003
        language_slug: str | None = None,
    ) -> QuerySet[Any]:
        """
        Include both regional and global (non-hidden) directories,
        matching the behavior of :meth:`Directory.search`.

        :param region: The region to filter by (optional)
        :param archived: Whether to include archived records (unused for directories)
        :param language_slug: Unused; directories are not language-specific
        :return: A filtered queryset
        """
        return cls.objects.filter(
            Q(region=region) | Q(region__isnull=True, is_hidden=False)
        )

    name = models.CharField(max_length=255, blank=False, verbose_name=_("name"))
    region = models.ForeignKey(
        Region,
        related_name="media_directories",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("region"),
    )
    parent = models.ForeignKey(
        "self",
        related_name="subdirectories",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name=_("parent directory"),
    )
    created_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("creation date"),
        help_text=_("The date and time when the directory was created"),
    )
    is_hidden = models.BooleanField(
        default=False,
        verbose_name=_("hidden"),
        help_text=_("Whether the directory is hidden in the regional media library"),
    )

    def serialize(self) -> dict[str, Any]:
        """
        This method creates a serialized version of that object for later use in AJAX and JSON.

        :return: The serialized representation of the directory
        """
        return {
            "type": "directory",
            "id": self.id,
            # Use empty string because preact-router only handles string parameters
            "parentId": self.parent.id if self.parent else "",
            "name": self.name,
            "CreatedDate": localize(timezone.localtime(self.created_date)),
            "isGlobal": not self.region,
            "numberOfEntries": self.subdirectories.count() + self.files.count(),
            "isHidden": self.is_hidden,
        }

    @classmethod
    def search(cls, region: Region, query: str) -> QuerySet[Directory]:
        """
        Searches for all directories which match the given `query` in their name.

        :param region: The searched region
        :param query: The query string used for filtering the regions
        :return: A query for all matching objects
        """
        return cls.objects.filter(
            Q(region=region) | Q(region__isnull=True, is_hidden=False),
            Q(name__icontains=query),
        )

    def __str__(self) -> str:
        """
        This overwrites the default Python __str__ method which would return <Directory object at 0xDEADBEEF>

        :return: The string representation (in this case the name) of the directory
        """
        return self.name

    def get_repr(self) -> str:
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<Directory: Directory object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the directory
        """
        region = f"region: {self.region.slug}" if self.region else "global"
        return f"<Directory (id: {self.id}, name: {self.name}, {region})>"

    class Meta:
        #: The verbose name of the model
        verbose_name = _("media directory")
        #: The plural verbose name of the model
        verbose_name_plural = _("media directories")
        #: The fields which are used to sort the returned objects of a QuerySet
        ordering = ["-region", "name"]
