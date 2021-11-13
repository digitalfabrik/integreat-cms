import logging

from django.contrib.auth import get_user_model

from .user_form import UserForm


logger = logging.getLogger(__name__)


class RegionUserForm(UserForm):
    """
    Form for creating and modifying region user objects
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = get_user_model()
        #: The fields of the model which should be handled by this form
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "is_active",
            "role",
            "send_activation_link",
            "organization",
            "expert_mode",
        ]
