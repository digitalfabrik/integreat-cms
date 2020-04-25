"""
Form for changing a user's email address
"""
import logging

from django import forms
from django.contrib.auth import get_user_model


logger = logging.getLogger(__name__)


class UserEmailForm(forms.ModelForm):

    class Meta:
        model = get_user_model()
        fields = ['email']
