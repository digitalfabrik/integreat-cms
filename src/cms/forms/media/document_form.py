from ..custom_model_form import CustomModelForm
from ...models import Document


class DocumentForm(CustomModelForm):
    """
    Form for creating and modifying document objects
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = Document
        #: The fields of the model which should be handled by this form
        fields = (
            "description",
            "document",
        )
