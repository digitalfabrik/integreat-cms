"""
Form for creating a user object
"""
import logging

from django import forms
from django.utils.translation import ugettext_lazy as _

from ...models import UserProfile
from ...utils.translation_utils import ugettext_many_lazy as __
from ..custom_model_form import CustomModelForm

logger = logging.getLogger(__name__)


class UserProfileForm(CustomModelForm):
    """
    Form for creating and modifying user profile objects
    """

    send_activation_link = forms.BooleanField(
        initial=True,
        required=False,
        label=_("Send activation link"),
        help_text=__(
            _(
                "Select this option to create an inactive user account and send an activation link per email to the user."
            ),
            _(
                "This link allows the user to choose a password and activates the account after confirmation."
            ),
        ),
    )

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = UserProfile
        #: The fields of the model which should be handled by this form
        fields = ["regions", "organization", "expert_mode"]

    def __init__(self, data=None, instance=None):

        # instantiate ModelForm
        super().__init__(data=data, instance=instance)

        # Remove activation link field if user already exists
        if self.instance.id:
            del self.fields["send_activation_link"]
