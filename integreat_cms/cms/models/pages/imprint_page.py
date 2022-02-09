import logging

from django.utils.translation import ugettext_lazy as _

from .imprint_page_translation import ImprintPageTranslation
from ..abstract_content_model import AbstractContentModel

logger = logging.getLogger(__name__)


class ImprintPage(AbstractContentModel):
    """
    Data model representing an imprint.
    """

    @staticmethod
    def get_translation_model():
        """
        Returns the translation model of this content model

        :return: The class of translations
        :rtype: type
        """
        return ImprintPageTranslation

    class Meta:
        #: The verbose name of the model
        verbose_name = _("imprint")
        #: The plural verbose name of the model
        verbose_name_plural = _("imprints")
        #: The name that will be used by default for the relation from a related object back to this one
        default_related_name = "imprints"
        #: The default permissions for this model
        default_permissions = ("change", "delete", "view")
