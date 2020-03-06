import os

from django.db import models
from django.utils.translation import ugettext_lazy as _

from ..regions.region import Region
from .directory import Directory
from .file import File
from ...utils.media_utils import get_thumbnail


class Document(models.Model):
    """
    The Document model is used to store basic information about files which are uploaded to the CMS. This is only a
    virtual document and does not necessarily exist on the actual file system. Each document is tied to a region via its
    directory.

    :param id: The database id of the document
    :param uploaded_at: The date and time when the document was uploaded

    Relationship fields:

    :param file: The file object of this document (related name: ``documents``)
    :param path: The directory containing this document (related name: ``documents``)
    :param region: The region to which this document belongs (related name: ``documents``)

    Reverse relationships:

    :param meta_data: The meta properties of this document
    """

    file = models.ForeignKey(
        File, related_name="documents", on_delete=models.CASCADE, null=True
    )
    name = models.CharField(max_length=255, blank=True, verbose_name=_("name"))
    path = models.ForeignKey(
        Directory, related_name="documents", on_delete=models.PROTECT, null=True
    )
    region = models.ForeignKey(
        Region, related_name="documents", on_delete=models.CASCADE, null=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(
        max_length=255, blank=True, verbose_name=_("description")
    )
    document = models.FileField(
        upload_to="",
        verbose_name=_("document"),
        help_text=_("The actual document file"),
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("uploaded date"),
        help_text=_("The date and time when the document was uploaded"),
    )

    def delete(self, using=None, keep_parents=False):
        """
        Deletes both the database entry and the actual file of a document.
        :param using: The alias of the database which should be used, defaults to ``DEFAULT_DB_ALIAS``
        :type using: str
        :param keep_parents: If the model is a sub-model of another, setting ``keep_parents = True`` will keep the data
                             in the parent database table, defaults to ``False``
        :type keep_parents: bool
        :return: The number of objects deleted and a dictionary with the number of deletions per object type.
        :rtype: tuple ( int, dict )
        """
        self.document.delete()
        return super().delete(using=using, keep_parents=keep_parents)

    def __str__(self):
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``Document object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the document
        :rtype: str
        """
        return os.path.basename(self.file.path)

    def thumbnail_path(self):
        return get_thumbnail(self.file, 300, 300, True)

    class Meta:
        #: The verbose name of the model
        verbose_name = _("document")
        #: The plural verbose name of the model
        verbose_name_plural = _("documents")
        #: The default permissions for this model
        default_permissions = ()
        permissions = (
            ("manage_documents", "Can manage documents"),
            ("can_delete_documents", "Can delete documents"),
        )
