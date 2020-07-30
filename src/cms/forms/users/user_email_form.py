import logging

from django import forms
from django.contrib.auth import get_user_model


logger = logging.getLogger(__name__)


class UserEmailForm(forms.ModelForm):
    """
    Form for modifying user email addresses
    """

    class Meta:
        model = get_user_model()
        fields = ["email"]
