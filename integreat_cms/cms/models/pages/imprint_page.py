import logging

from django.utils.translation import ugettext_lazy as _

from .imprint_page_translation import ImprintPageTranslation
from ..abstract_content_model import AbstractContentModel

logger = logging.getLogger(__name__)


class ImprintPage(AbstractContentModel):
    """
    Data model representing an imprint.
    """

    #: Whether translations should be returned in the default language if they do not exist
    fallback_translations_enabled = True

    @staticmethod
    def get_translation_model():
        """
        Returns the translation model of this content model

        :return: The class of translations
        :rtype: type
        """
        return ImprintPageTranslation

    @property
    def edit_lock_key(self):
        """
        This property returns the key that is used to lock this specific content object
        This overwrites :meth:`~integreat_cms.cms.models.abstract_content_model.AbstractContentModel.edit_lock_key`

        :return: A tuple of the region slug and the classname
        :rtype: tuple
        """
        return (self.region.slug, type(self).__name__)

    class Meta:
        #: The verbose name of the model
        verbose_name = _("imprint")
        #: The plural verbose name of the model
        verbose_name_plural = _("imprints")
        #: The name that will be used by default for the relation from a related object back to this one
        default_related_name = "imprints"
        #: The default permissions for this model
        default_permissions = ("change", "delete", "view")
