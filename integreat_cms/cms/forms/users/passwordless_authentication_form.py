from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UsernameField
from django.db.models import Q
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _

from ...utils.translation_utils import gettext_many_lazy as __


class PasswordlessAuthenticationForm(forms.Form):
    """
    Form class for authenticating users without using passwords but other authentication methods like FIDO2 or TOTP.
    """

    username = UsernameField(widget=forms.TextInput(attrs={"autofocus": True}))

    #: The user who tries to login without password
    user = None

    #: The different reasons why passwordless authentication might not be possible
    error_messages = {
        "invalid_login": _("The username or email address is incorrect."),
        "inactive": _("This account is inactive."),
        "disabled": __(
            _("Your account is not activated for passwordless authentication."),
            _("Please use the default login."),
        ),
        "not_available": _(
            "In order to use passwordless authentication, you have to configure at least one 2-factor authentication method."
        ),
    }

    def __init__(
        self,
        *args,
        request=None,
        **kwargs,
    ):
        r"""
        Render passwordless authentication form for HTTP GET requests

        :param request: Object representing the user call
        :type request: ~django.http.HttpRequest

        :param \*args: The supplied arguments
        :type \*args: list

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict
        """
        self.request = request
        super().__init__(*args, **kwargs)

        # Set the max length and label for the "username" field.
        self.username_field = get_user_model()._meta.get_field(
            get_user_model().USERNAME_FIELD
        )
        username_max_length = self.username_field.max_length or 254
        self.fields["username"].max_length = username_max_length
        self.fields["username"].widget.attrs["maxlength"] = username_max_length

    def clean_username(self):
        """
        Checks the input of the user to enable authentication

        :raises ~django.core.exceptions.ValidationError: If the given username or email is invalid

        :return: The cleaned username
        :rtype: str
        """
        username = self.cleaned_data.get("username")

        self.user = (
            get_user_model()
            .objects.filter(Q(username=username) | Q(email=username))
            .first()
        )

        # Check whether valid username was given
        if not self.user:
            raise ValidationError(
                self.error_messages["invalid_login"],
                code="invalid",
            )

        # Check whether the user is allowed to login
        if not self.user.is_active:
            raise ValidationError(
                self.error_messages["inactive"],
                code="inactive",
            )

        # Check whether the user is enabled for passwordless authentication
        if not self.user.passwordless_authentication_enabled:
            raise ValidationError(
                self.error_messages["disabled"],
                code="disabled",
            )

        # Check whether a 2-factor authentication method is available
        if not self.user.mfa_keys.exists() and not self.user.totp_key:
            raise ValidationError(
                self.error_messages["not_available"],
                code="not_available",
            )

        return username
