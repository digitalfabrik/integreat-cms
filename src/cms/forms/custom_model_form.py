from django import forms
from django.core.exceptions import FieldDoesNotExist
from django.utils.translation import ugettext_lazy as _
from django.utils.text import capfirst

from ..utils.text_utils import lowfirst


class CustomModelForm(forms.ModelForm):
    """
    Form for populating all text widgets of a ModelForm with the default placeholder "Enter ... here".
    Use this form as base class instead of :class:`django.forms.ModelForm`.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize placeholder model form

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :raises TypeError: If form is instantiated directly without an inheriting subclass
        """
        # Instantiate ModelForm
        try:
            super().__init__(*args, **kwargs)
        except ValueError as e:
            raise TypeError("CustomModelForm cannot be instantiated directly.") from e

        # Set placeholder for every text input fields
        for field_name in self.fields:
            field = self.fields[field_name]
            if isinstance(
                field.widget,
                (
                    forms.TextInput,
                    forms.Textarea,
                    forms.EmailInput,
                    forms.URLInput,
                    forms.PasswordInput,
                    forms.NumberInput,
                ),
            ):
                try:
                    # Use verbose_name of model field instead of field label because label is capitalized
                    # pylint: disable=no-member
                    model_field = self._meta.model._meta.get_field(
                        field_name
                    ).verbose_name
                except FieldDoesNotExist:
                    # In case field is not a model field, just use the label and make it lowercase
                    model_field = lowfirst(field.label)

                field.widget.attrs.update(
                    {"placeholder": capfirst(_("Enter {} here").format(model_field))}
                )
