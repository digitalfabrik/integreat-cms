import logging

from django import forms
from django.utils.translation import ugettext_lazy as _


logger = logging.getLogger(__name__)


class PlaceholderModelForm(forms.ModelForm):
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
            raise TypeError(
                "PlaceholderModelForm cannot be instantiated directly."
            ) from e

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
                # Use verbose_name of model field instead of field label because label is capitalized
                # pylint: disable=no-member
                model_field = self._meta.model._meta.get_field(field_name)
                field.widget.attrs.update(
                    {"placeholder": _("Enter {} here").format(model_field.verbose_name)}
                )

        logger.debug(
            "Default placeholders for form %s initialized", type(self).__name__
        )
