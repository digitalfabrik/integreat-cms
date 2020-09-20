import logging

from django.db import models

from .abstract_base_page import AbstractBasePage
from ..regions.region import Region

logger = logging.getLogger(__name__)


class ImprintPage(AbstractBasePage):
    """
    Data model representing an imprint.

    :param id: The database id of the imprint
    :param icon: The title image of the imprint

    Fields inherited from the :class:`~cms.models.pages.abstract_base_page.AbstractBasePage` model:

    :param archived: Whether or not the page is archived
    :param created_date: The date and time when the page was created
    :param last_updated: The date and time when the page was last updated

    Relationship fields:

    :param region: The region to which the imprint belongs (related name: ``imprints``)

    Reverse relationships:

    :param translations: The translations of this imprint
    """

    icon = models.ImageField(blank=True, null=True, upload_to="imprints/%Y/%m/%d")
    region = models.ForeignKey(
        Region, related_name="imprints", on_delete=models.CASCADE
    )

    class Meta:
        """
        This class contains additional meta configuration of the model class, see the
        `official Django docs <https://docs.djangoproject.com/en/2.2/ref/models/options/>`_ for more information.

        :param default_permissions: The default permissions for this model
        :type default_permissions: tuple

        :param permissions: The custom permissions for this model
        :type permissions: tuple
        """

        default_permissions = ()
        permissions = (("manage_imprint", "Can manage imprint"),)
