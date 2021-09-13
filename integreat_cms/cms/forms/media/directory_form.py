from ..custom_model_form import CustomModelForm
from ...models import Directory


class DirectoryForm(CustomModelForm):
    """
    Form for creating and modifying directory objects
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = Directory
        #: The fields of the model which should be handled by this form
        fields = ("name",)
