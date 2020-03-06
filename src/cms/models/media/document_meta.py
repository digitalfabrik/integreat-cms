from django.db import models
from cms.models.languages.language import Language
from cms.models.media.document import Document


class DocumentMeta(models.Model):
    """
    This model is used to store meta-data about :class:`~cms.models.media.document.Document` objects.

    :param id: The database id of the document meta
    :param property: The name of the meta property
    :param value: The value of the meta property

    Relationship fields:

    :param language: The language of this meta property (related name: ``document_meta_data``)
    :param document: The document this meta property belongs to (related name: ``meta_data``)
    """

    property = models.CharField(max_length=255, blank=False)
    value = models.TextField()
    language = models.ForeignKey(
        Language, related_name="document_meta_data", on_delete=models.CASCADE
    )
    document = models.ForeignKey(
        Document, related_name="meta_data", on_delete=models.CASCADE
    )

    def __str__(self):
        """
        This overwrites the default Python __str__ method which would return <DocumentMeta object at 0xDEADBEEF>
        :return: The string representation (in this case the key-value-pair) of the document meta property
        :rtype: str
        """
        return self.property + ": " + self.value

    class Meta:
        """
        This class contains additional meta configuration of the model class, see the
        `official Django docs <https://docs.djangoproject.com/en/2.2/ref/models/options/>`_ for more information.
        :param default_permissions: The default permissions for this model
        :type default_permissions: tuple
        """

        default_permissions = ()
