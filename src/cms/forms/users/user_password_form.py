"""
Form for changing a user's password
"""
import logging

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password, password_validators_help_texts
from django.utils.translation import ugettext as _


logger = logging.getLogger(__name__)


class UserPasswordForm(forms.ModelForm):

    old_password = forms.CharField(
        widget=forms.PasswordInput,
        help_text=password_validators_help_texts
    )

    new_password = forms.CharField(
        widget=forms.PasswordInput,
        validators=[validate_password],
        help_text=password_validators_help_texts
    )

    new_password_confirm = forms.CharField(
        widget=forms.PasswordInput,
        help_text=password_validators_help_texts
    )

    class Meta:
        model = get_user_model()
        fields = []

    # pylint: disable=signature-differs
    def save(self, *args, **kwargs):

        logger.info(
            'UserSettingsForm saved with args %s and kwargs %s',
            args,
            kwargs
        )

        # check if password field was changed
        if self.cleaned_data['new_password']:
            # change password
            self.instance.set_password(self.cleaned_data['new_password'])
            self.instance.save()

        return self.instance

    def clean(self):
        cleaned_data = super(UserPasswordForm, self).clean()
        old_password = cleaned_data.get("old_password")
        new_password = cleaned_data.get("new_password")
        new_password_confirm = cleaned_data.get("new_password_confirm")

        if not self.instance.check_password(old_password):
            self.add_error('old_password', _('Your old password is not correct.'))

        if new_password != new_password_confirm:
            self.add_error('new_password_confirm', _('The new passwords do not match.'))

        return cleaned_data
