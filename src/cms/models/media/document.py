import os

from django.db import models
from django.utils.translation import ugettext_lazy as _

from backend.settings import MEDIA_URL

from ...constants import allowed_media
from ...utils.media_utils import get_thumbnail
from ..regions.region import Region
from .directory import Directory


class Document(models.Model):
    """
    The Document model is used to store basic information about files which are uploaded to the CMS. This is only a
    virtual document and does not necessarily exist on the actual file system. Each document is tied to a region via its
    directory.
    """

    physical_path = models.CharField(
        max_length=255,
        blank=False,
        verbose_name=_("physical file path"),
    )
    type = models.CharField(
        choices=allowed_media.CHOICES,
        max_length=255,
        blank=False,
        verbose_name=_("file type"),
    )

    name = models.CharField(max_length=255, blank=False, verbose_name=_("name"))
    parent_directory = models.ForeignKey(
        Directory,
        related_name="documents",
        on_delete=models.PROTECT,
        null=True,
        verbose_name=_("parent directory"),
    )
    region = models.ForeignKey(
        Region,
        related_name="documents",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("region"),
    )
    alt_text = models.CharField(
        max_length=255, blank=True, verbose_name=_("description")
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("uploaded date"),
        help_text=_("The date and time when the document was uploaded"),
    )

    def __str__(self):
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``Document object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the document
        :rtype: str
        """
        return self.name

    def thumbnail_path(self):
        """
        This method calls the `get_thumbnail` method on the object and creates a default 300x300px thumbnail for it.

        :return: The physical path to the created thumbnail.
        :rtype: str
        """
        return get_thumbnail(self, 300, 300, False)

    def serialize(self):
        """
        This methods creates a serialized string of that document. This can later be used in the AJAX calls.

        :return: A serialized string representation of the document for JSON concatenation
        :rtype: str
        """
        return {
            "id": self.id,
            "name": self.name,
            "type": "file",
            "alt_text": self.alt_text,
            "file_type": self.type,
            "thumbnailPath": self.thumbnail_path(),
            "path": os.path.join(MEDIA_URL, self.physical_path),
            "uploadedAt": self.uploaded_at.strftime("%d/%m/%Y, %H:%M:%S"),
            "isGlobal": self.region is None,
        }

    def __repr__(self):
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<Document: Document object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the document
        :rtype: str
        """
        region = f", region: {self.region.slug}" if self.region else ""
        return f"<Document (id: {self.id}{region}, name: {self.name}, path: {self.physical_path})>"

    class Meta:
        #: The verbose name of the model
        verbose_name = _("document")
        #: The plural verbose name of the model
        verbose_name_plural = _("documents")
        #: The default permissions for this model
        default_permissions = ()
        #: The custom permissions for this model
        permissions = (
            ("manage_documents", "Can manage documents"),
            ("can_delete_documents", "Can delete documents"),
        )
