"""
This module contains the :class:`~integreat_cms.cms.models.media.media_file.MediaFile` model as well as the helper functions
:func:`~integreat_cms.cms.models.media.media_file.upload_path` and :func:`~integreat_cms.cms.models.media.media_file.upload_path_thumbnail` which
are used to determine the file system path to which the files should be uploaded.
"""

from __future__ import annotations

import logging
import time
from os.path import splitext
from time import strftime
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Exists, OuterRef, Q, Value
from django.db.models.functions import Concat
from django.template.defaultfilters import filesizeformat
from django.utils import timezone
from django.utils.formats import localize
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from linkcheck.models import Link, Url

from ...constants import allowed_media
from ..abstract_base_model import AbstractBaseModel
from ..regions.region import Region
from .directory import Directory

if TYPE_CHECKING:
    from typing import Any

    from django.db.models.fields.files import FieldFile
    from django.db.models.query import QuerySet

logger = logging.getLogger(__name__)


def upload_path(instance: MediaFile, filename: str) -> str:
    """
    This function calculates the path for a file which is uploaded to the media library.
    It contains the region id, the current year and month as subdirectories and the filename.
    It also contains the current epoch time to make sure that no path will be used twice.
    It is just the provisionally requested path for the media storage.
    If it already exists, Django will automatically append a random string to make sure the file name is unique.

    :param instance: The media library object
    :param filename: The filename of media library object
    :return: The upload path of the file
    """
    # If the media file is uploaded to a specific region, prepend a region id subdirectory
    subdirectory = f"regions/{instance.region.id}" if instance.region else "global"
    # Calculate the remaining upload path
    path = f"{subdirectory}/{strftime('%Y/%m')}/{int(time.time())}_{filename}"

    logger.debug("Upload path for media file %r: %r", instance.file, path)
    return path


# pylint: disable=unused-argument
def upload_path_thumbnail(instance: MediaFile, filename: str) -> str:
    """
    This function derives the upload path of a thumbnail file from it's original file.
    This makes it a bit easier to determine which thumbnail belongs to which file if there are multiple files with the
    same file name (in which case Django automatically appends a random string to the original's file name).

    E.g. if the files ``A.jpg`` and ``A_thumbnail.jpg`` already exist, and ``A.jpg`` is uploaded again, the resulting
    file names might be e.g. ``A_EOHRFQ2.jpg`` and ``A_thumbnail_IWxPiOq.jpg``, while with this function, the thumbnail
    will be stored as ``A_EOHRFQ2_thumbnail.jpg``, making it easier to examine these files on the file system.

    :param instance: The media library object
    :param filename: The (unused) initial filename of thumbnail
    :return: The upload path of the thumbnail
    """
    # Derive the thumbnail name from the original file name
    name, extension = splitext(instance.file.name)
    path = f"{name}_thumbnail{extension}"
    logger.debug("Upload path for thumbnail of %r: %r", instance.thumbnail, path)
    return path


def file_size_limit(value: FieldFile) -> None:
    """
    This function checks if the uploaded file exceeds the file size limit

    :param value: the size of upload file
    :raises ~django.core.exceptions.ValidationError: when the file size exceeds the size given in the settings.
    """
    if value.size > settings.MEDIA_MAX_UPLOAD_SIZE:
        raise ValidationError(
            _("File too large. Size should not exceed {}.").format(
                filesizeformat(settings.MEDIA_MAX_UPLOAD_SIZE)
            )
        )


class MediaFileQuerySet(models.QuerySet):
    """
    Custom queryset for media files
    """

    def filter_unused(self) -> MediaFileQuerySet:
        r"""
        Filter for unused media files

        :return: The queryset of unused media files
        """
        urls = Url.objects.filter(
            url=Concat(
                Value(settings.BASE_URL), Value(settings.MEDIA_URL), OuterRef("file")
            )
        )
        return self.annotate(is_embedded=Exists(urls)).filter(
            icon_organizations__isnull=True,
            icon_regions__isnull=True,
            events__isnull=True,
            pages__isnull=True,
            pois__isnull=True,
            is_embedded=False,
        )


class MediaFile(AbstractBaseModel):
    """
    The MediaFile model is used to store basic information about files which are uploaded to the CMS. This is only a
    virtual document and does not necessarily exist on the actual file system. Each document is tied to a region via its
    directory.
    """

    file = models.FileField(
        upload_to=upload_path,
        validators=[file_size_limit],
        verbose_name=_("file"),
        max_length=512,
    )
    thumbnail = models.FileField(
        upload_to=upload_path_thumbnail,
        validators=[file_size_limit],
        verbose_name=_("thumbnail file"),
        max_length=512,
    )
    file_size = models.IntegerField(verbose_name=_("file size"))
    type = models.CharField(
        choices=allowed_media.CHOICES,
        max_length=128,
        verbose_name=_("file type"),
    )
    name = models.CharField(max_length=512, verbose_name=_("name"))
    parent_directory = models.ForeignKey(
        Directory,
        related_name="files",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name=_("parent directory"),
    )
    region = models.ForeignKey(
        Region,
        related_name="files",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("region"),
    )
    alt_text = models.CharField(
        max_length=512, blank=True, verbose_name=_("description")
    )
    uploaded_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("uploaded date"),
        help_text=_("The date and time when the media file was uploaded"),
    )
    last_modified = models.DateTimeField(
        verbose_name=_("last modified"),
        help_text=_("The date and time when the physical media file was last modified"),
    )
    is_hidden = models.BooleanField(
        default=False,
        verbose_name=_("hidden"),
        help_text=_("Whether the media file is hidden in the regional media library"),
    )

    #: Custom model manager for media file objects
    objects = MediaFileQuerySet.as_manager()

    @property
    def url(self) -> str | None:
        """
        Returns the path of the physical file

        :return: The path of the file
        """
        return settings.BASE_URL + self.file.url if self.file else None

    @property
    def thumbnail_url(self) -> str | None:
        """
        Return the path of the image that should be used as the thumbnail.

        :return: The path of the file. If the file is an image and no thumbnail could be generated the file itself will be returned.
        """
        if not self.thumbnail:
            return self.url if self.type.startswith("image") else None
        return (
            f"{settings.BASE_URL}{self.thumbnail.url}?{self.last_modified.timestamp()}"
        )

    @cached_property
    def icon_usages(self) -> list[AbstractBaseModel]:
        """
        Check where a media file is used as icon

        :return: List of all objects that use this file as icon
        """
        return (
            list(self.icon_organizations.all())
            + list(self.icon_regions.all())
            + list(self.events.all())
            + list(self.pages.all())
            + list(self.pois.all())
        )

    @cached_property
    def is_icon(self) -> bool:
        """
        Check if a media file is used as icon

        :return: Whether a file is an icon
        """
        return bool(self.icon_usages)

    @cached_property
    def content_usages(self) -> QuerySet:
        """
        Check where this media file is embedded in the content

        :return: list with the search result
        """
        return Link.objects.filter(url__url=self.url).distinct("object_id")

    @cached_property
    def past_event_usages(self) -> QuerySet:
        """
        Count in how many past events this file is used

        :return: count of usages in past events
        """
        return self.events.filter(end__lt=timezone.now().date())

    @cached_property
    def is_only_used_in_past_events(self) -> QuerySet:
        """
        Check if a media file is used in past events only

        :return: if a media file is only used in past events
        """
        usage_counts = [
            self.past_event_usages.count(),
            (len(self.icon_usages) + self.content_usages.count()),
            self.events.count(),
        ]

        return all(c == usage_counts[0] for c in usage_counts)

    @cached_property
    def is_deletable(self) -> bool:
        """
        Check if a media file deletable

        :return: Whether a file is deletable
        """
        return not self.is_used or self.is_only_used_in_past_events

    @cached_property
    def is_embedded(self) -> bool:
        """
        Check if a media file is embedded in the content

        :return: Whether a file is embedded
        """
        return bool(self.content_usages)

    @cached_property
    def is_used(self) -> bool:
        """
        Check if a media file is used

        :return: Whether a file is used
        """
        return self.is_icon or self.is_embedded

    def serialize_usages(self) -> dict[str, Any]:
        """
        This methods creates a serialized dict of the file's usages. This can later be used in the AJAX calls.

        :return: A serialized dictionary representation of the file's usages
        """

        return {
            "isUsed": self.is_used,
            "iconUsages": [
                {
                    "url": settings.BASE_URL + icon_usage.backend_edit_link,
                    "name": f"{icon_usage}",
                    "title": f"{icon_usage._meta.verbose_name.title()}"
                    + (
                        f" ({icon_usage.region})"
                        if hasattr(icon_usage, "region")
                        and icon_usage.region != self.region
                        else ""
                    ),
                }
                for icon_usage in self.icon_usages
            ]
            or None,
            "contentUsages": [
                {
                    "url": settings.BASE_URL + link.content_object.backend_edit_link,
                    "name": f"{link.content_object}",
                    "title": f"{link.content_object.foreign_object._meta.verbose_name.title()}"
                    + (
                        f" ({link.content_object.foreign_object.region})"
                        if link.content_object.foreign_object.region != self.region
                        else ""
                    ),
                }
                for link in self.content_usages
            ]
            or None,
        }

    def serialize(self) -> dict[str, Any]:
        """
        This methods creates a serialized string of that document. This can later be used in the AJAX calls.

        :return: A serialized dictionary representation of the document for JSON concatenation
        """

        return {
            "id": self.id,
            "name": self.name,
            "altText": self.alt_text,
            "type": self.type,
            "typeDisplay": self.get_type_display(),
            "thumbnailUrl": self.thumbnail_url,
            "url": self.url,
            "fileSize": filesizeformat(self.file_size),
            "uploadedDate": localize(timezone.localtime(self.uploaded_date)),
            "lastModified": localize(timezone.localtime(self.last_modified)),
            "isGlobal": not self.region,
            "isHidden": self.is_hidden,
            "deletable": self.is_deletable,
        }

    @classmethod
    def search(cls, region: Region, query: str) -> QuerySet:
        """
        Searches for all media files which match the given `query` in their name.

        :param region: The searched region
        :param query: The query string used for filtering the media file
        :return: A queryset for all matching objects
        """
        return cls.objects.filter(
            Q(region=region) | Q(region__isnull=True, is_hidden=False),
            Q(name__icontains=query)
            | Q(alt_text__icontains=query)
            | Q(file__icontains=query),
        )

    def __str__(self) -> str:
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``MediaFile object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the document
        """
        return self.name

    def get_repr(self) -> str:
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<MediaFile: MediaFile object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the document
        """
        file_path = f"path: {self.file.path}, " if self.file else ""
        return (
            f"<MediaFile (id: {self.id}, name: {self.name}, {file_path}{self.region})>"
        )

    class Meta:
        #: The verbose name of the model
        verbose_name = _("media file")
        #: The plural verbose name of the model
        verbose_name_plural = _("media files")
        #: The fields which are used to sort the returned objects of a QuerySet
        ordering = ["-region", "name"]
        #: The default permissions for this model
        default_permissions = ("change", "delete", "view")
        #: The custom permissions for this model
        permissions = (
            ("upload_mediafile", "Can upload media file"),
            ("replace_mediafile", "Can replace media file"),
        )
