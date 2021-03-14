from django.db import models
from django.utils.translation import ugettext_lazy as _


class Document(models.Model):
    """
    The Document model is used to store meta-data about files which are uploaded to the CMS.
    """

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
        return self.document.name

    def __repr__(self):
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<Document: Document object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the document
        :rtype: str
        """
        return f"<Document (id: {self.id}, name: {self.document.name})>"

    class Meta:
        #: The verbose name of the model
        verbose_name = _("document")
        #: The plural verbose name of the model
        verbose_name_plural = _("documents")
        #: The default permissions for this model
        default_permissions = ()
