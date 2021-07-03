import logging


from .user_profile_form import UserProfileForm
from ...models import UserProfile


logger = logging.getLogger(__name__)


class RegionUserProfileForm(UserProfileForm):
    """
    Form for creating and modifying region user profile objects
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = UserProfile
        #: The fields of the model which should be handled by this form
        fields = ["organization", "expert_mode"]
