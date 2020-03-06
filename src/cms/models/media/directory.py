from django.db import models
from cms.models.regions.region import Region


class Directory(models.Model):
    """
    Model representing a directory containing documents. This is only a virtual directory and does not necessarily
    exist on the actual file system. Each directory is tied to a region.

    :param id: The database id of the directory
    :param name: The name of the directory

    Relationship fields:

    :param region: The region to which this directory belongs (related name: ``media_directories``)
    :param parent: The parent directory (related name: ``subdirectories``)

    Reverse relationships:

    :param subdirectories: The subdirectories of this directory
    :param documents: The documents in this directory
    """

    name = models.CharField(max_length=255, blank=False)
    region = models.ForeignKey(
        Region, related_name="media_directories", on_delete=models.CASCADE, null=True
    )
    parent = models.ForeignKey(
        "self",
        related_name="subdirectories",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )

    def __str__(self):
        """
        This overwrites the default Python __str__ method which would return <Document object at 0xDEADBEEF>
        :return: The string representation (in this case the name) of the directory
        :rtype: str
        """
        return self.name

    class Meta:
        """
        This class contains additional meta configuration of the model class, see the
        `official Django docs <https://docs.djangoproject.com/en/2.2/ref/models/options/>`_ for more information.
        :param default_permissions: The default permissions for this model
        :type default_permissions: tuple
        """

        default_permissions = ()
