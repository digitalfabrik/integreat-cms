from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.utils.translation import gettext_lazy as _

from ..abstract_content_model import AbstractContentModel
from .imprint_page_translation import ImprintPageTranslation

if TYPE_CHECKING:
    from django.db.models.base import ModelBase

logger = logging.getLogger(__name__)


class ImprintPage(AbstractContentModel):
    """
    Data model representing an imprint.
    """

    #: Whether translations should be returned in the default language if they do not exist
    fallback_translations_enabled: bool = True

    @staticmethod
    def get_translation_model() -> ModelBase:
        """
        Returns the translation model of this content model

        :return: The class of translations
        """
        return ImprintPageTranslation

    @property
    def edit_lock_key(self) -> tuple[int, str]:
        """
        This property returns the key that is used to lock this specific content object
        This overwrites :meth:`~integreat_cms.cms.models.abstract_content_model.AbstractContentModel.edit_lock_key`

        :return: A tuple of the region slug and the classname
        """
        return (self.region.id, type(self).__name__)

    class Meta:
        #: The verbose name of the model
        verbose_name = _("imprint")
        #: The plural verbose name of the model
        verbose_name_plural = _("imprints")
        #: The name that will be used by default for the relation from a related object back to this one
        default_related_name = "imprints"
        #: The default permissions for this model
        default_permissions = ("change", "delete", "view")
