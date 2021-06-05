import logging

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

        # Dynamically initialize logger to get module name of actual form
        self.logger = logging.getLogger(type(self).__module__)

        # Select the relevant attributes for logging
        attributes = []
        if self.data:
            attributes.append("data")
        if self.files:
            attributes.append("files")
        if self.instance.id:
            attributes.append("instance")

        self.logger.debug(
            "%s initialized"
            + (" with " + ": %r, ".join(attributes) + ": %r" if attributes else ""),
            type(self).__name__,
            *[getattr(self, attribute) for attribute in attributes]
        )

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

    def get_error_messages(self):
        """
        Return all error messages of this form and append labels to field-errors

        :return: The errors of this form
        :rtype: list
        """
        error_messages = []
        # Add field errors
        for field in self:
            for error in field.errors:
                error_messages.append(
                    {"type": "error", "text": field.label + ": " + error}
                )
        # Add non-field errors
        for error in self.non_field_errors():
            error_messages.append({"type": "error", "text": error})
        return error_messages

    def save(self, *args, **kwargs):
        """
        This method extends the default ``save()``-method of the base :class:`~django.forms.ModelForm` to provide debug
        logging

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The saved object returned by :ref:`topics-modelform-save`
        :rtype: object
        """
        self.logger.debug(
            "%s saved with cleaned data %r and changed data %r",
            type(self).__name__,
            self.cleaned_data,
            self.changed_data,
        )
        return super().save(*args, **kwargs)
