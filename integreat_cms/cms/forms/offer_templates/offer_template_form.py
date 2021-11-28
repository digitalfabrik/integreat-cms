from ..custom_model_form import CustomModelForm
from ...models import OfferTemplate
from ...utils.slug_utils import generate_unique_slug_helper


class OfferTemplateForm(CustomModelForm):
    """
    Form for creating and modifying offer template objects
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = OfferTemplate
        #: The fields of the model which should be handled by this form
        fields = ["name", "slug", "thumbnail", "url", "post_data", "use_postal_code"]

    def __init__(self, *args, **kwargs):
        r"""
        Initialize offer template form

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict
        """
        super().__init__(*args, **kwargs)

        self.fields["slug"].required = False

    def clean_slug(self):
        """
        Validate the slug field (see :ref:`overriding-modelform-clean-method`)

        :return: A unique slug based on the input value
        :rtype: str
        """
        return generate_unique_slug_helper(self, "offer-template")

    def clean_post_data(self):
        """
        Validate the post data field (see :ref:`overriding-modelform-clean-method`)

        :return: The valid post data
        :rtype: str
        """
        cleaned_post_data = self.cleaned_data["post_data"]
        if not cleaned_post_data:
            cleaned_post_data = {}
        return cleaned_post_data
