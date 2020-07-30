from django.db import models


class Document(models.Model):
    """
    The Document model is used to store meta-data about files which are uploaded to the CMS.

    :param id: The database id of the document
    :param description: The description of the document
    :param document: The actual document file
    :param uploaded_at: The date and time when the document was uploaded
    """

    description = models.CharField(max_length=255, blank=True)
    document = models.FileField(upload_to="")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def delete(self, using=None, keep_parents=False):
        """
        Deletes both the database entry and the actual file of a document.

        :param using: The alias of the database which should be used, defaults to ``DEFAULT_DB_ALIAS``
        :type using: str, optional

        :param keep_parents: If the model is a sub-model of another, setting ``keep_parents = True`` will keep the data
                             in the parent database table, defaults to ``False``
        :type keep_parents: bool, optional

        :return: The number of objects deleted and a dictionary with the number of deletions per object type.
        :rtype: tuple ( int, dict )
        """
        self.document.delete()
        super().delete(using=using, keep_parents=keep_parents)

    def __str__(self):
        """
        This overwrites the default Python __str__ method which would return <Document object at 0xDEADBEEF>

        :return: The string representation (in this case the filename) of the document
        :rtype: str
        """
        return self.document.name

    class Meta:
        """
        This class contains additional meta configuration of the model class, see the
        `official Django docs <https://docs.djangoproject.com/en/2.2/ref/models/options/>`_ for more information.

        :param default_permissions: The default permissions for this model
        :type default_permissions: tuple
        """

        default_permissions = ()
