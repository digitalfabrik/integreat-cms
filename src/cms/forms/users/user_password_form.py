import logging

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import (
    validate_password,
    password_validators_help_texts,
)
from django.utils.translation import ugettext_lazy as _


from ..custom_model_form import CustomModelForm

logger = logging.getLogger(__name__)


class UserPasswordForm(CustomModelForm):
    """
    Form for changing a user's password
    """

    old_password = forms.CharField(
        widget=forms.PasswordInput,
        label=_("My old password"),
        help_text=password_validators_help_texts,
    )

    new_password = forms.CharField(
        widget=forms.PasswordInput,
        validators=[validate_password],
        label=_("My new password"),
        help_text=password_validators_help_texts,
    )

    new_password_confirm = forms.CharField(
        widget=forms.PasswordInput,
        label=_("Confirm my new password"),
        help_text=password_validators_help_texts,
    )

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = get_user_model()
        #: The fields of the model which should be handled by this form
        fields = []

    def save(self, commit=True):
        """
        This method extends the default ``save()``-method of the base :class:`~django.forms.ModelForm` to set attributes
        which are not directly determined by input fields.

        :param commit: Whether or not the changes should be written to the database
        :type commit: bool

        :return: The saved user object
        :rtype: ~django.contrib.auth.models.User
        """

        # check if password field was changed
        if self.cleaned_data["new_password"]:
            # change password
            self.instance.set_password(self.cleaned_data["new_password"])
            self.instance.save()

        return self.instance

    def clean(self):
        """
        Validate form fields which depend on each other, see :meth:`django.forms.Form.clean`

        :return: The cleaned form data
        :rtype: dict
        """
        cleaned_data = super().clean()
        old_password = cleaned_data.get("old_password")
        new_password = cleaned_data.get("new_password")
        new_password_confirm = cleaned_data.get("new_password_confirm")

        if not self.instance.check_password(old_password):
            self.add_error("old_password", _("Your old password is not correct."))

        if new_password != new_password_confirm:
            self.add_error("new_password_confirm", _("The new passwords do not match."))

        logger.debug(
            "UserPasswordForm validated [2] with cleaned data %r", cleaned_data
        )
        return cleaned_data
