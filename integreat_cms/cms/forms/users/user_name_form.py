from __future__ import annotations

import logging

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from ..custom_model_form import CustomModelForm

logger = logging.getLogger(__name__)


class UserNameForm(CustomModelForm):
    """
    Form for modifying user name including username, first name, and last name.
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class,
        see the :class:`django.forms.ModelForm` for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = get_user_model()
        #: The fields of the model which should be handled by this form
        fields = ["username", "first_name", "last_name"]

    def clean_username(self) -> str:
        """
        Ensure that the username is unique across all users except the one being edited.

        :return: The validated username
        """
        username = self.cleaned_data.get("username")
        if (
            username
            and get_user_model()
            .objects.filter(username=username)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            self.add_error("username", _("This username is already taken."))
        return username
