from time import strftime
from django.db import models
from django.utils import timezone
from django.utils.formats import localize
from django.utils.translation import ugettext_lazy as _

from backend.settings import BASE_URL

from ...constants import allowed_media
from ..regions.region import Region
from .directory import Directory


def upload_directory(instance, filename):
    """
    The function sets the path for the media library. It contains the region id, the datestring and filename.

    :param instance: media library object
    :type instance: cms.models.media.media_file.MediaFile

    :param filename: filename of media library object
    :type filename: str

    :return: the directory path
    :rtype: str
    """
    datestring = strftime("%Y/%m")
    if instance and instance.region:
        path = f"sites/{instance.region.id}/{datestring}/{filename}"
    else:
        path = f"{datestring}/{filename}"
    return path


class MediaFile(models.Model):
    """
    The MediaFile model is used to store basic information about files which are uploaded to the CMS. This is only a
    virtual document and does not necessarily exist on the actual file system. Each document is tied to a region via its
    directory.
    """

    file = models.FileField(
        upload_to=upload_directory,
        verbose_name=_("file"),
        max_length=512,
    )
    thumbnail = models.FileField(
        upload_to=upload_directory,
        verbose_name=_("thumbnail file"),
        max_length=512,
    )
    type = models.CharField(
        choices=allowed_media.CHOICES,
        max_length=64,
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

    @property
    def url(self):
        """
        Returns the path of the physical file

        :return: The path of the file
        :rtype: str
        """
        return BASE_URL + self.file.url if self.file else None

    def serialize(self):
        """
        This methods creates a serialized string of that document. This can later be used in the AJAX calls.

        :return: A serialized string representation of the document for JSON concatenation
        :rtype: str
        """
        return {
            "id": self.id,
            "name": self.name,
            "altText": self.alt_text,
            "type": self.type,
            "typeDisplay": self.get_type_display(),
            "thumbnailUrl": BASE_URL + self.thumbnail.url if self.thumbnail else None,
            "url": self.url,
            "uploadedDate": localize(timezone.localtime(self.uploaded_date)),
            "isGlobal": not self.region,
        }

    def __str__(self):
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``MediaFile object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the document
        :rtype: str
        """
        return self.name

    def __repr__(self):
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<MediaFile: MediaFile object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the document
        :rtype: str
        """
        region = f"region: {self.region.slug}" if self.region else "global"
        return f"<MediaFile (id: {self.id}, name: {self.name}, path: {self.file.path}, {region})>"

    class Meta:
        #: The verbose name of the model
        verbose_name = _("media file")
        #: The plural verbose name of the model
        verbose_name_plural = _("media files")
        #: The fields which are used to sort the returned objects of a QuerySet
        ordering = ["-region", "name"]
