from django.db import models


class File(models.Model):
    """
    Model representing an actual file object in the file system. It can be part of multiple
    :class:`~cms.models.media.document.Document` objects and thus be contained in the media library of multiple regions.

    :param id: The database id of the file
    :param hash: The hashsum of the file
    :param path: The file path
    :param type: The file type

    Reverse relationships:

    :param documents: All document objects belonging to this file
    """

    hash = models.CharField(max_length=255, blank=False, unique=True)
    path = models.CharField(max_length=255, blank=False)
    type = models.CharField(max_length=255, blank=False)

    def __str__(self):
        """
        This overwrites the default Python __str__ method which would return <File object at 0xDEADBEEF>
        :return: The string representation (in this case the filepath) of the file
        :rtype: str
        """
        return self.path

    class Meta:
        """
        This class contains additional meta configuration of the model class, see the
        `official Django docs <https://docs.djangoproject.com/en/2.2/ref/models/options/>`_ for more information.
        :param default_permissions: The default permissions for this model
        :type default_permissions: tuple
        """

        default_permissions = ()
