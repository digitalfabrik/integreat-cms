import logging

from django.utils.translation import ugettext_lazy as _

from .abstract_base_page import AbstractBasePage
from ..languages.language import Language

logger = logging.getLogger(__name__)


class ImprintPage(AbstractBasePage):
    """
    Data model representing an imprint.
    """

    @property
    def languages(self):
        """
        This property returns a list of all :class:`~integreat_cms.cms.models.languages.language.Language` objects, to
        which an imprint translation exists.

        :return: list of all :class:`~integreat_cms.cms.models.languages.language.Language` an imprint is translated into
        :rtype: list [ ~integreat_cms.cms.models.languages.language.Language ]
        """
        return Language.objects.filter(imprint_translations__page=self)

    class Meta:
        #: The verbose name of the model
        verbose_name = _("imprint")
        #: The plural verbose name of the model
        verbose_name_plural = _("imprints")
        #: The name that will be used by default for the relation from a related object back to this one
        default_related_name = "imprint"
        #: The default permissions for this model
        default_permissions = ("change", "delete", "view")
