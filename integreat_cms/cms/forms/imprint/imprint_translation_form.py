import logging

from ...models import ImprintPageTranslation
from ..custom_content_model_form import CustomContentModelForm


logger = logging.getLogger(__name__)


class ImprintTranslationForm(CustomContentModelForm):
    """
    Form for creating and modifying imprint translation objects
    """

    class Meta:
        model = ImprintPageTranslation
        fields = ["title", "status", "content", "minor_edit"]
