import logging
from django import forms
from django.utils.translation import gettext_lazy as _

from ...models import Organization
from ..icon_widget import IconWidget
from ..custom_model_form import CustomModelForm
from ...utils.slug_utils import generate_unique_slug_helper


logger = logging.getLogger(__name__)


class OrganizationForm(CustomModelForm):
    """
    Form for creating and modifying organization objects
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = Organization
        #: The fields of the model which should be handled by this form
        fields = [
            "name",
            "slug",
            "icon",
        ]
        #: The widgets which are used in this form
        widgets = {
            "icon": IconWidget(),
        }

    def __init__(self, **kwargs):
        r"""
        Initialize organization form

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict
        """
        super().__init__(**kwargs)
        self.fields["slug"].required = False

    def clean_slug(self):
        """
        Validate the slug field (see :ref:`overriding-modelform-clean-method`)

        :return: A unique slug based on the input value
        :rtype: str
        """
        return generate_unique_slug_helper(self, "organization")

    def clean_name(self):
        """
        Validate if form fields name is not already in use for another organization in the same region
        (see :ref:`overriding-modelform-clean-method`)
        :return: The name which is unique per region
        :rtype: str
        """
        cleaned_name = self.cleaned_data["name"]
        if (
            Organization.objects.exclude(id=self.instance.id)
            .filter(region=self.instance.region, name=cleaned_name)
            .exists()
        ):
            self.add_error(
                "name",
                forms.ValidationError(
                    _(
                        "An organization with the same name already exists in this region. Please choose another name."
                    ),
                    code="invalid",
                ),
            )
        return cleaned_name
