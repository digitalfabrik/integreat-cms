from django import forms
from django.utils.translation import gettext_lazy as _


class AuthenticationForm(forms.Form):
    """
    Form to check the password of an already authenticated user. Used for critical operations where a valid session
    might not be enough (e.g. modifying 2-FA options).
    """

    password = forms.CharField(widget=forms.PasswordInput(), label=_("Password"))
