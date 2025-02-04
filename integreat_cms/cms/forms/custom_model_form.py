from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django import forms
from django.contrib import messages
from django.core.exceptions import FieldDoesNotExist
from django.utils import translation
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _

from ..utils.text_utils import lowfirst

if TYPE_CHECKING:
    from typing import Any

    from django.http import HttpRequest


class CustomModelForm(forms.ModelForm):
    """
    Form for populating all text widgets of a ModelForm with the default placeholder "Enter ... here".
    Use this form as base class instead of :class:`django.forms.ModelForm`.
    """

    def __init__(self, **kwargs: Any) -> None:
        r"""
        Initialize placeholder model form

        :param \**kwargs: The supplied keyword arguments
        :raises TypeError: If form is instantiated directly without an inheriting subclass
        """
        # pop kwarg to make sure the super class does not get this params
        disabled = kwargs.pop("disabled", False)
        additional_instance_attributes = kwargs.pop(
            "additional_instance_attributes",
            {},
        )

        # Instantiate ModelForm
        try:
            super().__init__(**kwargs)
        except ValueError as e:
            raise TypeError("CustomModelForm cannot be instantiated directly.") from e

        # Set additional instance attributes
        for name, value in additional_instance_attributes.items():
            setattr(self.instance, name, value)

        # Dynamically initialize logger to get module name of actual form
        self.logger = logging.getLogger(type(self).__module__)

        # Select the relevant attributes for logging
        attributes = []
        if self.data:
            attributes.append("data")
        if self.files:
            attributes.append("files")
        if self.initial:
            attributes.append("initial")
        if self.instance.id:
            attributes.append("instance")

        self.logger.debug(
            "%s initialized"
            + (" with " + ": %r, ".join(attributes) + ": %r" if attributes else ""),
            type(self).__name__,
            *[getattr(self, attribute) for attribute in attributes],
        )

        for field_name, field in self.fields.items():
            # If form is disabled, disable all form fields
            if disabled:
                field.disabled = True

            # Set placeholder for every text input fields
            if isinstance(
                field.widget,
                forms.TextInput
                | forms.Textarea
                | forms.EmailInput
                | forms.URLInput
                | forms.PasswordInput
                | forms.NumberInput,
            ):
                try:
                    # Use verbose_name of model field instead of field label because label is capitalized
                    model_field = self._meta.model._meta.get_field(
                        field_name,
                    ).verbose_name
                except FieldDoesNotExist:
                    # In case field is not a model field, just use the label and make it lowercase
                    model_field = lowfirst(field.label)

                field.widget.attrs.update(
                    {"placeholder": capfirst(_("Enter {} here").format(model_field))},
                )

    def clean(self) -> dict[str, Any]:
        """
        This method extends the default ``clean()``-method of the base :class:`~django.forms.ModelForm` to provide debug
        logging

        :return: The cleaned data (see :ref:`overriding-modelform-clean-method`)
        """
        # Validate ModelForm
        cleaned_data = super().clean()
        self.logger.debug(
            "%s validated with cleaned data %r",
            type(self).__name__,
            cleaned_data,
        )
        return cleaned_data

    def save(self, commit: bool = True) -> Any:
        """
        This method extends the default ``save()``-method of the base :class:`~django.forms.ModelForm` to provide debug
        logging

        :param commit: Whether or not the changes should be written to the database
        :return: The saved object returned by :ref:`django:topics-modelform-save`
        """
        self.logger.debug(
            "%s saved with changed data %r",
            type(self).__name__,
            self.changed_data,
        )
        # Update submitted data with cleaned data if changes are saved
        self.data = self.cleaned_data

        # Save ModelForm
        return super().save(commit=commit)

    def add_error_messages(self, request: HttpRequest) -> None:
        """
        This function accepts the current request and adds the form's error messages to the message queue of
        :mod:`django.contrib.messages`.

        :param request: The current request submitting the form
        """
        # Add field errors
        for field in self:
            for error in field.errors:
                messages.error(request, _(field.label) + ": " + _(error))
        # Add non-field errors
        for error in self.non_field_errors():
            messages.error(request, _(error))
        # Add debug logging in english
        with translation.override("en"):
            self.logger.debug(
                "%r submitted with errors: %r",
                type(self).__name__,
                self.errors,
            )

    def get_error_messages(self) -> list[dict[str, str]]:
        """
        Return all error messages of this form and append labels to field-errors

        :return: The errors of this form
        """
        error_messages = []
        # Add field errors
        for field in self:
            for error in field.errors:
                error_messages.append(
                    {"type": "error", "text": field.label + ": " + error},
                )
        # Add non-field errors
        for error in self.non_field_errors():
            error_messages.append({"type": "error", "text": error})
        return error_messages
