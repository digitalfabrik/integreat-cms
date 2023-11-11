from __future__ import annotations

import logging

from ...models import ImprintPageTranslation
from ..custom_content_model_form import CustomContentModelForm

logger = logging.getLogger(__name__)


class ImprintTranslationForm(CustomContentModelForm):
    """
    Form for creating and modifying imprint translation objects
    """

    class Meta(CustomContentModelForm.Meta):
        model = ImprintPageTranslation
