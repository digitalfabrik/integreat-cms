from __future__ import annotations

import logging

from django import forms
from django.utils.translation import gettext_lazy as _

from ...models import MediaFile
from ..custom_model_form import CustomModelForm

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

    def clean(self) -> dict:
        """
        Validate form fields which depend on each other, see :meth:`django.forms.Form.clean`:
        If the file is moved to another region, add a :class:`~django.core.exceptions.ValidationError`.

        :return: The cleaned form data
        """
        cleaned_data = super().clean()

        if (
            (parent := cleaned_data.get("parent_directory"))
            and self.instance
            and parent.region != self.instance.region
        ):
            self.add_error(
                "parent_directory",
                forms.ValidationError(
                    _("The file cannot be moved to a directory of another region."),
                    code="invalid",
                ),
            )

        return cleaned_data
