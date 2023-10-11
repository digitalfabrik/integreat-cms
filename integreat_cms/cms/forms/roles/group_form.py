from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth.models import Group

from ..custom_model_form import CustomModelForm

if TYPE_CHECKING:
    from typing import Any


class GroupForm(CustomModelForm):
    """
    Form for creating and modifying user group objects
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = Group
        #: The fields of the model which should be handled by this form
        fields = ["permissions"]

    def __init__(self, **kwargs: Any) -> None:
        # Instantiate CustomModelForm
        super().__init__(**kwargs)
        self.fields["permissions"].widget.attrs["size"] = "20"
