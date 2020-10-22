import logging

from django.conf import settings
from django.db import models

from backend.settings import IMPRINT_SLUG
from .abstract_base_page_translation import AbstractBasePageTranslation

from .imprint_page import ImprintPage
from ..languages.language import Language


logger = logging.getLogger(__name__)


class ImprintPageTranslation(AbstractBasePageTranslation):
    """
    Data model representing a imprint translation

    :param id: The database id of the imprint translation

    Fields inherited from the :class:`~cms.models.pages.abstract_base_page_translation.AbstractBasePageTranslation` model:

    :param status: The status of the imprint translation (choices: :mod:`cms.constants.status`)
    :param title: The title of the imprint translation
    :param text: The content of the imprint translation
    :param currently_in_translation: Flag to indicate a translation is being updated by an external translator
    :param version: The revision number of the imprint translation
    :param minor_edit: Flag to indicate whether the difference to the previous revision requires an update in other
                       languages
    :param created_date: The date and time when the imprint translation was created
    :param last_updated: The date and time when the imprint translation was last updated

    Relationship fields:

    :param page: The imprint page the translation belongs to (related name: ``translations``)
    :param language: The language of the imprint translation (related name: ``imprint_translations``)
    :param creator: The user who created the imprint translation (related name: ``imprint_translations``)
    """

    page = models.ForeignKey(
        ImprintPage, related_name="translations", on_delete=models.CASCADE
    )
    language = models.ForeignKey(
        Language, related_name="imprint_translations", on_delete=models.CASCADE
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="imprint_translations",
        null=True,
        on_delete=models.SET_NULL,
    )

    @property
    def permalink(self):
        """
        This property calculates the permalink dynamically

        :return: The permalink of the imprint
        :rtype: str
        """
        return "/".join(
            filter(
                None,
                [self.page.region.slug, self.language.code, IMPRINT_SLUG],
            )
        )

    @property
    def slug(self):
        """
        For compatibility with the other page translations, a slug property is useful.

        :return: pseudo slug for the imprint translation
        :rtype: str
        """
        return settings.IMPRINT_SLUG

    def __str__(self):
        """
        This overwrites the default Python __str__ method which would return <ImprintPageTranslation object at 0xDEADBEEF>

        :return: The string representation of the imprint page translation with information about the most important
                 fields (useful for debugging purposes)
        :rtype: str
        """
        if self.id:
            return f"(id: {self.id}, page_id: {self.page.id}, lang: {self.language.code}, version: {self.version})"
        return super().__str__()

    class Meta:
        """
        This class contains additional meta configuration of the model class, see the
        `official Django docs <https://docs.djangoproject.com/en/2.2/ref/models/options/>`_ for more information.

        :param ordering: The fields which are used to sort the returned objects of a QuerySet
        :type ordering: list [ str ]

        :param default_permissions: The default permissions for this model
        :type default_permissions: tuple
        """

        ordering = ["page", "-version"]
        default_permissions = ()
