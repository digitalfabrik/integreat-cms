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

    def save(self, *args, **kwargs):
        """
        This method extends the default ``save()``-method of the base :class:`~django.forms.ModelForm` to set attributes
        which are not directly determined by input fields.

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The saved user profile object
        :rtype: ~cms.models.users.user_profile.UserProfile
        """
        # pop kwarg to make sure the super class does not get this param
        region = kwargs.pop("region", None)

        # check if instance exists now because after save() from UserProfileForm it will exist anyway
        instance_exists = bool(self.instance.id)

        # save UserProfileForm
        user_profile = super().save(*args, **kwargs)

        if not instance_exists:
            # only update the region when user is created
            user_profile.regions.add(region)
            user_profile.save()
            logger.info("%r was added to %r", user_profile, region)

        return user_profile
