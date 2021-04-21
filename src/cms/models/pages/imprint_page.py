import logging

from django.db import models
from django.utils.translation import ugettext_lazy as _

from .abstract_base_page import AbstractBasePage
from ..languages.language import Language
from ..regions.region import Region

logger = logging.getLogger(__name__)


class ImprintPage(AbstractBasePage):
    """
    Data model representing an imprint.
    """

    region = models.OneToOneField(
        Region,
        related_name="imprint",
        on_delete=models.CASCADE,
        verbose_name=_("region"),
    )

    class Meta:
        #: The verbose name of the model
        verbose_name = _("imprint")
        #: The plural verbose name of the model
        verbose_name_plural = _("imprints")
        #: The default permissions for this model
        default_permissions = ()
        #: The custom permissions for this model
        permissions = (("manage_imprint", "Can manage imprint"),)

    @property
    def languages(self):
        """
        This property returns a list of all :class:`~cms.models.languages.language.Language` objects, to which an
        imprint translation exists.

        :return: list of all :class:`~cms.models.languages.language.Language` an imprint is translated into
        :rtype: list [ ~cms.models.languages.language.Language ]
        """
        return Language.objects.filter(imprint_translations__page=self)
