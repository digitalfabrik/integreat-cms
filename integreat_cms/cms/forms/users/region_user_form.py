import logging

from django.contrib.auth import get_user_model

from ...models import Organization
from .user_form import UserForm


logger = logging.getLogger(__name__)


class RegionUserForm(UserForm):
    """
    Form for creating and modifying region user objects
    """

    def __init__(self, region, **kwargs):
        r"""
        Initialize region user form

        :param region: The current region
        :type region: ~integreat_cms.cms.models.regions.region.Region

        :param \**kwargs: The supplied keyword arguments
        :type \**kwargs: dict
        """

        # Instantiate UserForm
        super().__init__(**kwargs)

        if self.instance.id:
            # If the user exists, limit organization choices to the user's regions
            self.fields["organization"].queryset = Organization.objects.filter(
                region__in=self.instance.regions.all()
            )
        else:
            # If the user does not yet exist, only allow the current region
            self.fields["organization"].queryset = region.organizations.all()

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
