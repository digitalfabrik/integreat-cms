import logging

from django import forms
from django.db.models import Q
from django.utils.translation import gettext as _

from ...models import Directory
from ..custom_model_form import CustomModelForm

logger = logging.getLogger(__name__)


class CreateDirectoryForm(CustomModelForm):
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
        fields = (
            "name",
            "parent",
        )

    def clean(self):
        """
        This function provides additional validation rules for the directory form.

        :return: The cleaned data
        :rtype: dict
        """
        cleaned_data = super().clean()

        if cleaned_data.get("parent"):
            if cleaned_data.get("parent").region != self.instance.region:
                self.add_error(
                    "parent",
                    forms.ValidationError(
                        _(
                            "The directory cannot be created in a directory of another region."
                        ),
                        code="invalid",
                    ),
                )

        queryset = Directory.objects
        if self.instance.region:
            # If directory is created for a region, only limit choices to the global library and the regional one
            queryset = queryset.filter(
                Q(region=self.instance.region) | Q(region__isnull=True)
            )
        if queryset.filter(
            parent=cleaned_data.get("parent"),
            name=cleaned_data.get("name"),
        ).exists():
            self.add_error(
                "name",
                forms.ValidationError(
                    _('A directory with the name "{}" already exists.').format(
                        cleaned_data.get("name")
                    ),
                    code="invalid",
                ),
            )

        logger.debug(
            "CreateDirectoryForm validated [2] with cleaned data %r", cleaned_data
        )
        return cleaned_data
