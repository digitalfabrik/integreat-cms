import logging

from django import forms
from django.contrib.auth import get_user_model


logger = logging.getLogger(__name__)


class UserEmailForm(forms.ModelForm):
    """
    Form for modifying user email addresses
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = get_user_model()
        #: The fields of the model which should be handled by this form
        fields = ["email"]
