import logging

from ...models import POITranslation
from ..custom_content_model_form import CustomContentModelForm


logger = logging.getLogger(__name__)


class POITranslationForm(CustomContentModelForm):
    """
    Form for creating and modifying POI translation objects
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = POITranslation
        #: The fields of the model which should be handled by this form
        fields = CustomContentModelForm.Meta.fields + ["meta_description", "slug"]

    def __init__(self, **kwargs):
        r"""
        Initialize POI translation form

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict
        """

        # Pop kwarg to make sure the super class does not get this param
        default_language_title = kwargs.pop("default_language_title", None)

        # Instantiate CustomContentModelForm
        super().__init__(**kwargs)

        if default_language_title:
            self.fields["title"].initial = default_language_title
