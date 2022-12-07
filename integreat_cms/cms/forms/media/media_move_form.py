import logging

from django import forms
from django.utils.translation import gettext as _

from ..custom_model_form import CustomModelForm
from ...models import MediaFile

logger = logging.getLogger(__name__)


class MediaMoveForm(CustomModelForm):
    """
    Form for moving media file objects into a directory
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = MediaFile
        #: The fields of the model which should be handled by this form
        fields = ("parent_directory",)

    def clean(self):
        """
        Validate form fields which depend on each other, see :meth:`django.forms.Form.clean`:
        If the file is moved to another region, add a :class:`~django.core.exceptions.ValidationError`.

        :return: The cleaned form data
        :rtype: dict
        """
        cleaned_data = super().clean()

        if cleaned_data.get("parent_directory"):
            if cleaned_data.get("parent_directory").region != self.instance.region:
                self.add_error(
                    "parent_directory",
                    forms.ValidationError(
                        _("The file cannot be moved to a directory of another region."),
                        code="invalid",
                    ),
                )

        return cleaned_data
